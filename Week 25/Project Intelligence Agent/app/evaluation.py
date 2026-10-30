from __future__ import annotations

import json
from pathlib import Path

from app.agent import ProjectAgent


def evaluate(evaluation_path: Path, project_path: Path) -> dict:
    dataset = json.loads(Path(evaluation_path).read_text(encoding="utf-8"))
    rows = []
    tp = fp = fn = exact = citation_expected = citation_present = 0
    for case in dataset["cases"]:
        result = ProjectAgent(project_path).investigate(case["request"])
        expected = set(case["expected_finding_ids"])
        actual = {f["id"] for f in result["findings"]}
        case_tp, case_fp, case_fn = len(expected & actual), len(actual - expected), len(expected - actual)
        tp += case_tp; fp += case_fp; fn += case_fn
        exact += int(expected == actual)
        for finding_id in expected:
            citation_expected += 1
            finding = next((f for f in result["findings"] if f["id"] == finding_id), None)
            citation_present += int(bool(finding and finding["sources"]))
        rows.append({"case_id": case["id"], "expected": sorted(expected), "actual": sorted(actual),
                     "true_positives": case_tp, "false_positives": case_fp,
                     "false_negatives": case_fn, "exact_match": expected == actual})
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"dataset": dataset["dataset_name"], "method": "synthetic labeled scenario set; deterministic retrieval and rule-based evidence extraction",
            "cases": len(rows), "micro_precision": round(precision, 4), "micro_recall": round(recall, 4),
            "micro_f1": round(f1, 4), "exact_scenario_accuracy": round(exact / len(rows), 4),
            "expected_finding_citation_coverage": round(citation_present / citation_expected, 4) if citation_expected else 1.0,
            "counts": {"true_positive": tp, "false_positive": fp, "false_negative": fn},
            "limitations": ["All cases and labels are synthetic and authored with the dataset.",
                            "Metrics measure only the included rule-based demonstration; they do not estimate performance on real projects.",
                            "The evaluation has no independent human adjudication or statistical confidence interval."],
            "case_results": rows}
