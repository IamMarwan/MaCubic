from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.main import DB_PATH, import_paths, read_register  # noqa: E402


def main() -> None:
    db = DB_PATH
    if db.exists():
        db.unlink()
    folder = ROOT / "fixtures" / "development"
    paths = sorted([*folder.glob("*.pdf"), *folder.glob("*.xlsx")],
                   key=lambda p: ("amendment" in p.name.lower(), p.name.lower()))
    first_import = import_paths(paths)
    rows = read_register()
    repeated_import = import_paths(paths)
    reference = json.loads((ROOT / "annotations" / "development_reference.json").read_text(encoding="utf-8"))
    expected = {row["id"]: row for row in reference["requirements"]}
    by_id = {row["requirement_id"]: row for row in rows}
    matched = 0
    wrong_values: list[str] = []
    unsupported: list[str] = []
    invalid_sources: list[str] = []
    for rid, exp in expected.items():
        got = by_id.get(rid)
        if not got:
            continue
        exact = (got["description"] == exp["description"] and got["category"] == exp["category"]
                 and got["status"] == exp["status"] and got["quantity"] == (exp["quantity"] if isinstance(exp["quantity"], (int, float)) else None)
                 and got["unit"] == (None if exp["unit"] == "unknown" else exp["unit"])
                 and got["threshold"] == (None if exp["threshold"] == "unknown" else exp["threshold"])
                 and got["deadline"] == (None if exp["deadline"] == "unknown" else exp["deadline"])
                 and got["revision"] == exp["rev"])
        if exact:
            matched += 1
        else:
            wrong_values.append(rid)
        if not got["source"].get("quotation"):
            invalid_sources.append(rid)
        if (got["source"].get("file") != exp.get("source_file")
                or got["source"].get("page") != exp.get("source_page")):
            invalid_sources.append(rid)
        if any(v == "known" and got.get(k) is None for k, v in got["value_state"].items()):
            unsupported.append(rid)
    omissions = sorted(set(expected) - set(by_id))
    precision = matched / len(by_id) if by_id else 0
    recall = matched / len(expected) if expected else 0
    conflicts_expected = set(reference["seeded_conflicts"])
    conflicts_found = {r["requirement_id"] for r in rows if r["conflict"]}
    result = {
        "benchmark": reference["benchmark"],
        "method": "Stable-ID match with exact normalized description, category, status, quantity, unit, threshold, deadline, and revision checks; source file/page and quotation are checked for validity. Explicit unknowns are compared as null values.",
        "counts": {"reference_requirements": len(expected), "final_register_requirements": len(by_id),
                   "matched": matched, "duplicates_in_source_rows": first_import["duplicates_in_upload"],
                   "omissions": len(omissions), "wrong_values": len(wrong_values),
                   "unsupported_inferences": len(unsupported), "invalid_source_references": len(invalid_sources),
                   "seeded_conflicts": len(conflicts_expected), "conflicts_flagged": len(conflicts_found & conflicts_expected)},
        "precision": round(precision, 4), "recall": round(recall, 4),
        "precision_formula": "matched final register entries / final register entries",
        "recall_formula": "matched final register entries / reference entries",
        "mandatory_and_deadline_mismatches": [r for r in wrong_values if r in by_id and expected.get(r, {}).get("status") != by_id[r]["status"]],
        "omitted_ids": omissions, "wrong_value_ids": wrong_values, "unsupported_inference_ids": unsupported,
        "invalid_source_ids": invalid_sources, "unflagged_conflict_ids": sorted(conflicts_expected - conflicts_found),
        "repeat_import": {"inserted": repeated_import["inserted"], "updated": repeated_import["updated"],
                          "register_count_after_repeat": len(read_register())},
        "interpretation": "Deterministic fixture-format result only. It is not evidence of performance on unstructured or real procurement packages."
    }
    output = ROOT / "annotations" / "evaluation_report.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md = ["# Development benchmark evaluation", "", f"Benchmark: `{result['benchmark']}`", "",
          f"- Precision: **{result['precision']:.0%}** ({matched}/{len(by_id)})",
          f"- Recall: **{result['recall']:.0%}** ({matched}/{len(expected)})",
          f"- Source-row duplicate IDs (including the explicitly revised REQ-08): {first_import['duplicates_in_upload']}",
          f"- Omissions: {len(omissions)}; wrong values: {len(wrong_values)}; unsupported inferences: {len(unsupported)}; invalid source references: {len(invalid_sources)}",
          f"- Seeded conflicts flagged: {len(conflicts_found & conflicts_expected)}/{len(conflicts_expected)}",
          f"- Re-import: {repeated_import['inserted']} inserted, {repeated_import['updated']} updated; register remains at {len(read_register())} entries.", "",
          "Precision is matched final register entries divided by final register entries. Recall is matched final register entries divided by annotated reference entries. A match requires exact description, category, mandatory/optional status, quantity, unit, threshold, deadline, revision, and expected source file/page after explicit unknown values are normalized to null. REQ-08's reference reflects the explicitly superseding amendment.", "",
          "**Limit:** this fixed synthetic corpus uses tagged requirement rows. The score does not measure extraction quality on arbitrary tender PDFs, handwriting, scans, or prose.", ""]
    (ROOT / "annotations" / "evaluation_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
