from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.analysis import ANNOTATIONS, STATUSES, best_requirement_match, build_matrix, read_reference, status_for  # noqa: E402


def main() -> None:
    matrix, deviations, clarifications = build_matrix()
    with (ANNOTATIONS / "labeled_90_pairs.csv").open(encoding="utf-8-sig", newline="") as handle:
        labels = {row["pair_id"]: row for row in csv.DictReader(handle)}
    confusion = {expected: {predicted: 0 for predicted in STATUSES} for expected in STATUSES}
    for pair in matrix:
        confusion[pair["gold_status"]][pair["status"]] += 1
    total = len(matrix)
    correct = sum(confusion[s][s] for s in STATUSES)
    per_status = {}
    for status in STATUSES:
        tp = confusion[status][status]
        fp = sum(confusion[other][status] for other in STATUSES if other != status)
        fn = sum(confusion[status][other] for other in STATUSES if other != status)
        support = sum(confusion[status].values())
        per_status[status] = {"support": support, "correct": tp,
            "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
            "f1": round(2 * tp / (2 * tp + fp + fn), 4) if 2 * tp + fp + fn else 0.0}

    reqs = read_reference()["requirements"]
    adversarial = json.loads((ANNOTATIONS / "adversarial_cases.json").read_text(encoding="utf-8"))
    semantic_results = []
    for case in adversarial:
        result = {"case": case["case"]}
        if "expected_requirement_id" in case:
            actual, score = best_requirement_match(case["text"], reqs)
            result.update({"expected": case["expected_requirement_id"], "actual": actual,
                          "score": round(score, 3), "passed": actual == case["expected_requirement_id"]})
        elif case["case"] == "contradiction":
            status, conflict, _ = status_for([
                {"quotation": "Our technical schedule confirms full compliance with REQ-20."},
                {"quotation": "We exclude these changes and will not supply the omitted technical departures."}])
            result.update({"expected": case["expected_status"], "actual": status,
                           "contradiction_flagged": conflict, "passed": status == case["expected_status"] and conflict})
        else:
            status, _, _ = status_for([])
            result.update({"expected": case["expected_status"], "actual": status, "passed": status == case["expected_status"]})
        semantic_results.append(result)

    mandatory_met_without_evidence = [row["pair_id"] for row in matrix
        if row["mandatory"] and row["status"] == "met" and not row["bid_evidence"]]
    missing_tender_sources = [row["pair_id"] for row in matrix if not row["tender_reference"]["quotation"]]
    missing_bid_sources = [row["pair_id"] for row in matrix
        if row["status"] in {"met", "partially met", "not met", "not applicable"} and not row["bid_evidence"]]
    by_pair = {row["pair_id"]: row for row in matrix}
    seeded = {
        "exclusion": "cedar_build::REQ-04",
        "alternative_proposal": "cedar_build::REQ-11",
        "delivery_deviation": "northstar_works::REQ-16",
        "warranty_gap": "summit_contracting::REQ-23",
        "contradiction": "summit_contracting::REQ-20",
    }
    seeded_findings = {name: {"pair_id": pair_id, "surfaced": name in by_pair[pair_id]["finding_flags"]}
                       for name, pair_id in seeded.items()}

    report = {
        "benchmark": "week2-development-90-pairs-v1",
        "matching_policy": "Stable requirement IDs are preferred when present. ID-free passages are mapped by normalized token overlap, curated terminology synonyms, and fuzzy phrase similarity. Status decisions use explicit commitments, limitations, refusals, justified scope exclusions, and contradictory passages; ambiguous or absent evidence is not evidenced.",
        "counts": {"labeled_pairs": len(labels), "analyzed_pairs": total, "exact_matches": correct,
                   "exact_status_agreement": round(correct / total, 4) if total else 0,
                   "deviation_findings": len(deviations), "clarification_questions": len(clarifications),
                   "mandatory_met_without_bid_evidence": len(mandatory_met_without_evidence),
                   "missing_tender_source_references": len(missing_tender_sources),
                   "unsupported_substantive_bid_findings": len(missing_bid_sources)},
        "per_status": per_status,
        "confusion_matrix": confusion,
        "seeded_findings": seeded_findings,
        "semantic_and_adversarial_cases": semantic_results,
        "failures": {"mandatory_met_without_evidence": mandatory_met_without_evidence,
                     "missing_tender_sources": missing_tender_sources,
                     "unsupported_bid_findings": missing_bid_sources,
                     "unsurfaced_seeded_findings": [name for name, item in seeded_findings.items() if not item["surfaced"]],
                     "failed_adversarial_cases": [item["case"] for item in semantic_results if not item["passed"]]},
        "limitation": "Results are for a synthetic, manually labeled package and a transparent rule-based baseline; they do not establish accuracy on arbitrary or real-world tender submissions."
    }
    (ANNOTATIONS / "working_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (ANNOTATIONS / "deviation_register.json").write_text(json.dumps(deviations, indent=2), encoding="utf-8")
    with (ANNOTATIONS / "clarification_questions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["bidder", "requirement_id", "category", "status", "mandatory", "question", "tender_source", "bid_source"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(clarifications)
    (ANNOTATIONS / "evaluation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = ["# Week 2 benchmark evaluation", "", f"- Labeled bidder-requirement pairs: **{len(labels)}**",
          f"- Exact status agreement: **{correct}/{total} ({report['counts']['exact_status_agreement']:.1%})**",
          f"- Deviation findings: **{len(deviations)}**; clarification questions: **{len(clarifications)}**", "",
          "## Per-status results", "", "| Status | Support | Correct | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|---:|"]
    for status in STATUSES:
        metrics = per_status[status]
        md.append(f"| {status} | {metrics['support']} | {metrics['correct']} | {metrics['precision']:.1%} | {metrics['recall']:.1%} | {metrics['f1']:.1%} |")
    md += ["", "## Confusion matrix", "", "Rows are manual labels; columns are predicted statuses.", "",
           "| Expected \\ Predicted | " + " | ".join(STATUSES) + " |", "|---|" + "---:|" * len(STATUSES)]
    for expected in STATUSES:
        md.append("| " + expected + " | " + " | ".join(str(confusion[expected][pred]) for pred in STATUSES) + " |")
    md += ["", "## Adversarial checks", ""]
    for item in semantic_results:
        md.append(f"- `{item['case']}`: {'PASS' if item['passed'] else 'FAIL'} (expected {item['expected']}; got {item['actual']}).")
    md += ["", "## Acceptance checks", ""]
    for name, item in seeded_findings.items():
        md.append(f"- Seeded {name.replace('_', ' ')}: {'surfaced' if item['surfaced'] else 'MISSING'} (`{item['pair_id']}`).")
    md += [f"- Mandatory met findings without bid evidence: {len(mandatory_met_without_evidence)}.",
           f"- Missing tender source references: {len(missing_tender_sources)}.",
           f"- Unsupported substantive bid findings: {len(missing_bid_sources)}.", "",
           f"**Method:** {report['matching_policy']}", "",
           f"**Limit:** {report['limitation']}", ""]
    (ANNOTATIONS / "evaluation_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))
    print("Per-status:", json.dumps(per_status, indent=2))
    print("Adversarial checks:", json.dumps(semantic_results, indent=2))


if __name__ == "__main__":
    main()
