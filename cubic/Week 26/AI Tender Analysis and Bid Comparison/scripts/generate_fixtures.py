from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "fixtures" / "development"
RESERVED = ROOT / "fixtures" / "week4_reserved"
ANN = ROOT / "annotations"


def make_requirements(count: int, prefix: str = "REQ") -> list[dict]:
    categories = ["Scope", "Technical", "Submission", "Deadline", "Commercial", "Exclusion", "Evaluation"]
    rows = []
    for i in range(1, count + 1):
        status = "optional" if i in {5, 18, 26} and count >= 26 else "mandatory"
        category = categories[(i - 1) % len(categories)]
        quantity = 1 if category == "Submission" else (i * 10 if category == "Scope" else "unknown")
        unit = "package" if category == "Submission" else ("m2" if category == "Scope" else "unknown")
        threshold = {"Technical": "minimum 90%", "Commercial": "maximum 60 days", "Evaluation": "minimum 70 points"}.get(category, "unknown")
        deadline = "2026-12-15T17:00+04:00" if category == "Deadline" else "unknown"
        desc = f"Provide the {category.lower()} evidence package item {i:02d} for tender TND-2026-041."
        requirement_id = f"REQ-W4-{i:02d}" if prefix == "W4" else f"REQ-{i:02d}"
        rows.append({"id": requirement_id, "category": category, "description": desc,
                     "status": status, "quantity": quantity, "unit": unit, "threshold": threshold,
                     "deadline": deadline, "rev": "1"})
    return rows


def req_line(row: dict) -> str:
    return (f"{row['id']} | {row['category']} | {row['description']} | {row['status']} | "
            f"quantity={row['quantity']} | unit={row['unit']} | threshold={row['threshold']} | "
            f"deadline={row['deadline']} | rev={row['rev']}")


def write_pdf(path: Path, title: str, lines: list[str], rows_per_page: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page_size = landscape(letter)
    c = canvas.Canvas(str(path), pagesize=page_size)
    width, height = page_size
    for page_index in range(0, max(1, len(lines)), rows_per_page):
        chunk = lines[page_index:page_index + rows_per_page]
        c.setTitle(title)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(24, height - 35, title)
        c.setFont("Helvetica", 5.5)
        y = height - 58
        for line in chunk:
            # Keep each tagged record on one extractable text line.
            c.drawString(24, y, line[:1500])
            y -= 28
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(42, 28, "Synthetic training fixture · searchable text · not a real tender")
        c.showPage()
    c.save()


def write_boq(path: Path, count: int, prefix: str) -> list[list]:
    wb = Workbook()
    ws = wb.active
    ws.title = "BOQ"
    ws.append(["BOQ ID", "Description", "Quantity", "Unit", "Unit Rate (AED)", "Line Total (AED)"])
    for i in range(1, count + 1):
        qty = i * 5
        rate = 25 + i * 2
        ws.append([f"{prefix}-BOQ-{i:02d}", f"Synthetic work item {i:02d}", qty, "m2", rate, f"=C{i+1}*E{i+1}"])
    format_sheet(ws)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return [[f"{prefix}-BOQ-{i:02d}", f"Synthetic work item {i:02d}", i * 5, "m2", 25 + i * 2, (i * 5) * (25 + i * 2)] for i in range(1, count + 1)]


def write_bid(path: Path, bidder: str, count: int, prefix: str, delta: int) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Bid BOQ"
    ws.append(["BOQ ID", "Description", "Quantity", "Unit", "Bid Unit Rate (AED)", "Quoted Total (AED)"])
    for i in range(1, count + 1):
        qty = i * 5
        rate = 25 + i * 2 + delta
        ws.append([f"{prefix}-BOQ-{i:02d}", f"Synthetic work item {i:02d}", qty, "m2", rate, qty * rate])
    meta = wb.create_sheet("Bid Summary")
    meta.append(["Field", "Value"])
    meta.append(["Bidder", bidder])
    meta.append(["Currency", "AED"])
    meta.append(["Payment terms", "unknown" if delta == 0 else f"{30 + delta} days"])
    meta.append(["Offer validity", "90 days"])
    compliance = wb.create_sheet("Compliance")
    compliance.append(["Requirement ID", "Compliance label", "Bidder note"])
    for i in range(1, count + 1):
        label = "partial" if (i + delta) % 7 == 0 else "compliant"
        note = "Clarification required" if label == "partial" else "Evidence included in synthetic submission"
        rid = f"REQ-W4-{i:02d}" if prefix == "W4" else f"REQ-{i:02d}"
        compliance.append([rid, label, note])
    for sheet in wb.worksheets:
        format_sheet(sheet)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def format_sheet(ws) -> None:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="145B61")
        cell.alignment = Alignment(wrap_text=True)
    for column, width in {"A": 20, "B": 55, "C": 14, "D": 12, "E": 20, "F": 22}.items():
        ws.column_dimensions[column].width = width


def freeze_package(folder: Path, count: int, prefix: str, n_bids: int, title: str) -> dict:
    reqs = make_requirements(count, prefix)
    lines = [req_line(row) for row in reqs]
    write_pdf(folder / f"{prefix.lower()}_tender_requirements.pdf", title, lines, 5)
    boq = write_boq(folder / f"{prefix.lower()}_boq.xlsx", count, prefix)
    bid_files = []
    compliance_labels = {}
    commercial_calculations = {}
    for n in range(n_bids):
        bidder = f"Bidder {chr(65+n)}"
        filename = f"{prefix.lower()}_bidder_{chr(97+n)}.xlsx"
        delta = n * 3
        write_bid(folder / filename, bidder, count, prefix, delta)
        bid_files.append(filename)
        compliance_labels[bidder] = {
            row["id"]: ("partial" if (index + delta) % 7 == 0 else "compliant")
            for index, row in enumerate(reqs, start=1)
        }
        subtotal = sum((i * 5) * (25 + i * 2 + delta) for i in range(1, count + 1))
        contingency = round(subtotal * 0.05, 2)
        commercial_calculations[bidder] = {"currency": "AED", "line_total_subtotal": subtotal,
                                           "contingency_rate": 0.05, "contingency_amount": contingency,
                                           "evaluated_total": round(subtotal + contingency, 2),
                                           "payment_terms_days": None if delta == 0 else 30 + delta,
                                           "offer_validity_days": 90}
    boq_mappings = {row["id"]: f"{prefix}-BOQ-{index:02d}" for index, row in enumerate(reqs, start=1)}
    return {"tender_id": prefix, "requirements": reqs, "boq": boq,
            "bid_files": bid_files, "compliance_labels": compliance_labels,
            "boq_mappings": boq_mappings, "commercial_calculations": commercial_calculations}


def main() -> None:
    DEV.mkdir(parents=True, exist_ok=True)
    RESERVED.mkdir(parents=True, exist_ok=True)
    ANN.mkdir(parents=True, exist_ok=True)
    dev = make_requirements(30)
    write_pdf(DEV / "tender_requirements.pdf", "TND-2026-041 · Development Tender Requirements",
              [req_line(row) for row in dev], 6)
    amendment_lines = [
        "AMENDMENT A-01 | Issued 2026-11-12 | Tender addendum",
        "CONFLICT | REQ-03 | Base requirement and addendum state different minimum insurance coverage; no precedence is stated.",
        "SUPERSEDES | REQ-08 | Amendment A-01 expressly supersedes clause TND-08 revision 1; revised threshold is 75 points.",
        "REQ-08 | Evaluation | Meet the revised technical evaluation threshold of 75 points under amendment A-01. | mandatory | quantity=unknown | unit=unknown | threshold=minimum 75 points | deadline=unknown | rev=2",
        "CONFLICT | REQ-21 | Base clause allows 60-day payment; addendum states 45 days; precedence is not stated.",
    ]
    write_pdf(DEV / "tender_amendment_A01.pdf", "TND-2026-041 · Amendment A-01", amendment_lines, 8)
    write_boq(DEV / "tender_boq.xlsx", 30, "DEV")
    for n, bidder in enumerate(["Northstar Works", "Cedar Build", "Summit Contracting"]):
        write_bid(DEV / f"bid_{chr(97+n)}_{bidder.lower().replace(' ', '_')}.xlsx", bidder, 30, "DEV", n * 3)

    effective_dev = [dict(row) for row in dev]
    effective_dev[7].update({"category": "Evaluation",
                             "description": "Meet the revised technical evaluation threshold of 75 points under amendment A-01.",
                             "quantity": "unknown", "unit": "unknown", "threshold": "minimum 75 points",
                             "deadline": "unknown", "rev": "2", "source_file": "tender_amendment_A01.pdf", "source_page": 1})
    for index, row in enumerate(effective_dev, start=1):
        if row["id"] != "REQ-08":
            row["source_file"] = "tender_requirements.pdf"
            row["source_page"] = ((index - 1) // 6) + 1
    dev_reference = {"benchmark": "development-v1", "requirements": effective_dev,
                     "seeded_conflicts": ["REQ-03", "REQ-21"],
                     "supersession": {"REQ-08": {"supersedes": "TND-08 revision 1", "revision": "2", "threshold": "minimum 75 points"}}}
    (ANN / "development_reference.json").write_text(json.dumps(dev_reference, indent=2), encoding="utf-8")
    reserved_reference = freeze_package(RESERVED, 10, "W4", 2, "WEEK 4 RESERVED · Frozen Tender Reference")
    (RESERVED / "FROZEN_REFERENCE.json").write_text(json.dumps(reserved_reference, indent=2), encoding="utf-8")
    (RESERVED / "README.md").write_text(
        "# Reserved Week 4 test package\n\nThis package is reserved for Week 4 evaluation. The tender, 10 requirement answers, 10 BOQ lines, and two bid submissions are generated together. Treat `FROZEN_REFERENCE.json` as read-only and do not tune development extraction rules against this package.\n",
        encoding="utf-8")
    print(f"Generated fixtures under {DEV} and {RESERVED}")


if __name__ == "__main__":
    main()
