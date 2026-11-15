from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from openpyxl import load_workbook

from .schemas import RegisterExport, Requirement, SourceReference

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
DB_PATH = DATA / "register.db"
SUPPORTED = {".pdf", ".xlsx"}
app = FastAPI(title="AI Tender Analysis and Bid Comparison", version="1.0.0")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS requirements (
        requirement_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, payload TEXT NOT NULL,
        imported_at TEXT NOT NULL)""")
    return db


def parse_fields(parts: list[str]) -> dict[str, Any]:
    values = {"category": parts[1].strip(), "description": parts[2].strip(), "status": parts[3].strip().lower()}
    for raw in parts[4:]:
        if "=" not in raw:
            continue
        key, value = raw.strip().split("=", 1)
        values[key.strip().lower()] = value.strip()
    for key in ["unit", "threshold", "deadline"]:
        if values.get(key, "").strip().lower() == "unknown":
            values[key] = None
    if values["status"] not in {"mandatory", "optional", "unknown"}:
        values["status"] = "unknown"
    try:
        values["quantity"] = float(values["quantity"]) if values.get("quantity") else None
    except ValueError:
        values["quantity"] = None
    return values


def extract_pdf(path: Path, display_name: str) -> tuple[list[dict], list[str], list[dict]]:
    found: list[dict] = []
    controls: list[str] = []
    page_texts: list[dict] = []
    try:
        doc = fitz.open(path)
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text("text")
            page_texts.append({"page": page_no, "text": text})
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if line.startswith(("CONFLICT |", "SUPERSEDES |")):
                    controls.append(line)
                if not re.match(r"^REQ-[A-Z0-9-]+\s*\|", line):
                    continue
                parts = [part.strip() for part in line.split("|")]
                if len(parts) < 4:
                    continue
                found.append({"id": parts[0], "fields": parse_fields(parts), "quote": line,
                              "document": path.stem, "file": display_name, "kind": "pdf_page", "page": page_no})
    except Exception as exc:
        raise HTTPException(400, f"Could not read PDF '{display_name}': {exc}") from exc
    if not any(p["text"].strip() for p in page_texts):
        raise HTTPException(400, f"PDF '{display_name}' has no searchable text layer; scanned PDFs are not supported.")
    return found, controls, page_texts


def extract_xlsx(path: Path, display_name: str) -> tuple[list[dict], list[str], list[dict]]:
    found: list[dict] = []
    controls: list[str] = []
    cells: list[dict] = []
    try:
        book = load_workbook(path, data_only=True, read_only=True)
        for sheet in book.worksheets:
            for row in sheet.iter_rows():
                values = [cell.value for cell in row]
                if not values:
                    continue
                first = str(values[0]).strip() if values[0] is not None else ""
                if first.startswith(("CONFLICT |", "SUPERSEDES |")):
                    controls.append(first)
                if not re.match(r"^REQ-[A-Z0-9-]+$", first):
                    continue
                text_values = [str(v).strip() if v is not None else "" for v in values]
                if len(text_values) < 4:
                    continue
                found.append({"id": first, "fields": parse_fields([first] + text_values[1:]),
                              "quote": " | ".join(text_values), "document": path.stem,
                              "file": display_name, "kind": "spreadsheet_cell", "sheet": sheet.title,
                              "cell": row[0].coordinate})
            # Record a small source index for the source-viewer endpoint.
            cells.append({"sheet": sheet.title, "max_row": sheet.max_row, "max_column": sheet.max_column})
    except Exception as exc:
        raise HTTPException(400, f"Could not read XLSX '{display_name}': {exc}") from exc
    return found, controls, cells


def source_is_valid(item: dict) -> bool:
    if item["kind"] == "pdf_page":
        return item.get("page", 0) > 0 and bool(item.get("quote"))
    return bool(item.get("sheet") and item.get("cell") and item.get("quote"))


def import_paths(paths: list[Path], names: list[str] | None = None) -> dict:
    extracted: list[dict] = []
    control_lines: list[dict] = []
    source_index: dict[str, Any] = {}
    for index, path in enumerate(paths):
        display_name = names[index] if names else path.name
        if path.suffix.lower() not in SUPPORTED:
            raise HTTPException(400, f"Unsupported file type '{path.suffix or '(none)'}' for '{display_name}'. Upload PDF or XLSX.")
        if path.suffix.lower() == ".pdf":
            rows, controls, pages = extract_pdf(path, display_name)
            source_index[display_name] = {"type": "pdf", "pages": pages}
        else:
            rows, controls, sheets = extract_xlsx(path, display_name)
            source_index[display_name] = {"type": "xlsx", "sheets": sheets}
        extracted.extend(rows)
        control_lines.extend({"file": display_name, "line": line} for line in controls)

    # Controls are applied only when the source explicitly identifies an affected requirement.
    conflict_notes: dict[str, list[str]] = {}
    supersession: dict[str, list[str]] = {}
    revision_history: dict[str, list[dict[str, str]]] = {}
    for control in control_lines:
        line = control["line"]
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        if parts[0] == "CONFLICT" and re.match(r"^REQ-[A-Z0-9-]+$", parts[1]):
            conflict_notes.setdefault(parts[1], []).append(" ".join(parts[2:]))
        elif parts[0] == "SUPERSEDES" and re.match(r"^REQ-[A-Z0-9-]+$", parts[1]):
            supersession.setdefault(parts[1], []).append(" ".join(parts[2:]))
            revision_history.setdefault(parts[1], []).append({"source_file": control["file"], "statement": line})

    valid: list[dict] = []
    for item in extracted:
        if not source_is_valid(item):
            continue
        fields = item["fields"]
        raw = "|".join([item["id"], fields.get("description", "")]).strip().lower()
        fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        source_args = {"document": item["document"], "file": item["file"], "location_type": item["kind"],
                       "quotation": item["quote"], "page": item.get("page"), "sheet": item.get("sheet"),
                       "cell": item.get("cell")}
        payload = Requirement(
            requirement_id=item["id"], category=fields.get("category", "unknown"),
            description=fields.get("description", ""), status=fields.get("status", "unknown"),
            quantity=fields.get("quantity"), unit=fields.get("unit"), threshold=fields.get("threshold"),
            deadline=fields.get("deadline"),
            value_state={key: ("known" if fields.get(key) not in (None, "", "unknown") else "unknown")
                         for key in ["quantity", "unit", "threshold", "deadline"]},
            source=SourceReference(**source_args), revision=fields.get("rev", "1"),
            supersedes=supersession.get(item["id"], []), conflict=bool(conflict_notes.get(item["id"])),
            revision_history=revision_history.get(item["id"], []),
            conflict_note="; ".join(conflict_notes.get(item["id"], [])) or None,
            imported_at=now_iso(), fingerprint=fingerprint)
        valid.append(payload.model_dump())

    duplicate_ids = len(valid) - len({item["requirement_id"] for item in valid})
    # Keep the latest occurrence in this batch (e.g., an amendment row after the base tender).
    final_by_id = {item["requirement_id"]: item for item in valid}
    inserted = updated = 0
    with connect() as db:
        for item in final_by_id.values():
            old = db.execute("SELECT fingerprint FROM requirements WHERE requirement_id=?", (item["requirement_id"],)).fetchone()
            if old and old["fingerprint"] == item["fingerprint"]:
                continue
            db.execute("INSERT INTO requirements(requirement_id,fingerprint,payload,imported_at) VALUES(?,?,?,?) "
                       "ON CONFLICT(requirement_id) DO UPDATE SET fingerprint=excluded.fingerprint,payload=excluded.payload,imported_at=excluded.imported_at",
                       (item["requirement_id"], item["fingerprint"], json.dumps(item), item["imported_at"]))
            if old:
                updated += 1
            else:
                inserted += 1
    return {"extracted": len(valid), "inserted": inserted, "updated": updated,
            "duplicates_in_upload": duplicate_ids, "conflicts_flagged": len(conflict_notes),
            "controls_seen": len(control_lines), "sources": source_index}


def read_register() -> list[dict]:
    with connect() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT payload FROM requirements ORDER BY requirement_id")]


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (ROOT / "app" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": app.title, "version": app.version}


@app.get("/api/register")
def register() -> dict:
    entries = read_register()
    return RegisterExport(generated_at=now_iso(), count=len(entries), requirements=entries).model_dump()


@app.get("/api/export.json")
def export_json() -> dict:
    return register()


@app.get("/api/export.csv")
def export_csv() -> StreamingResponse:
    entries = read_register()
    output = io.StringIO(newline="")
    fields = ["requirement_id", "category", "description", "status", "quantity", "unit", "threshold", "deadline",
              "revision", "conflict", "conflict_note", "source_document", "source_file", "source_location", "quotation"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        source = entry["source"]
        location = f"page {source['page']}" if source.get("page") else f"{source.get('sheet')}!{source.get('cell')}"
        writer.writerow({**entry, "source_document": source["document"], "source_file": source["file"],
                         "source_location": location, "quotation": source["quotation"]})
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=tender-register.csv"})


@app.post("/api/ingest")
async def ingest(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(400, "Choose one or more PDF or XLSX files.")
    UPLOADS.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    names: list[str] = []
    for upload in files:
        name = Path(upload.filename or "upload").name
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED:
            raise HTTPException(400, f"Unsupported file '{name}'. Upload PDF or XLSX.")
        target = UPLOADS / name
        content = await upload.read()
        if not content:
            raise HTTPException(400, f"File '{name}' is empty.")
        target.write_bytes(content)
        paths.append(target)
        names.append(name)
    if not any(path.suffix.lower() == ".pdf" for path in paths):
        raise HTTPException(400, "No tender requirement rows found: include a searchable PDF or an XLSX with REQ-ID rows.")
    return import_paths(paths, names)


@app.post("/api/load-development-fixture")
def load_development_fixture() -> dict:
    folder = ROOT / "fixtures" / "development"
    if not folder.exists():
        raise HTTPException(500, "Development fixture package is missing.")
    paths = sorted([*folder.glob("*.pdf"), *folder.glob("*.xlsx")],
                   key=lambda p: ("amendment" in p.name.lower(), p.name.lower()))
    if not paths:
        raise HTTPException(500, "Development fixture package is empty. Run scripts/generate_fixtures.py.")
    return import_paths(paths)


@app.get("/api/source/{filename}")
def source(filename: str) -> dict:
    safe_name = Path(filename).name
    path = UPLOADS / safe_name
    if not path.exists():
        fixture = ROOT / "fixtures" / "development" / safe_name
        path = fixture if fixture.exists() else path
    if not path.exists():
        raise HTTPException(404, "Source file not found in this local workspace.")
    if path.suffix.lower() == ".pdf":
        try:
            doc = fitz.open(path)
            return {"file": safe_name, "type": "pdf", "pages": [{"page": n + 1, "text": page.get_text("text")} for n, page in enumerate(doc)]}
        except Exception as exc:
            raise HTTPException(400, f"Could not open PDF source: {exc}") from exc
    try:
        book = load_workbook(path, data_only=True, read_only=True)
        return {"file": safe_name, "type": "xlsx", "sheets": [{"sheet": sheet.title,
                "rows": [[cell.value for cell in row] for row in sheet.iter_rows()]} for sheet in book.worksheets]}
    except Exception as exc:
        raise HTTPException(400, f"Could not open spreadsheet source: {exc}") from exc


@app.delete("/api/register")
def clear_register() -> dict:
    with connect() as db:
        db.execute("DELETE FROM requirements")
    return {"deleted": True, "count": 0}
