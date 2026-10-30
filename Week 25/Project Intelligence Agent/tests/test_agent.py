from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from app.agent import ProjectAgent
from app.evaluation import evaluate


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = ProjectAgent(ROOT / "data" / "project.json")

    def test_full_investigation_has_trace_and_cited_findings(self):
        result = self.agent.investigate("Analyze all major outstanding issues, risks, actions, and conflicts")
        self.assertGreaterEqual(len(result["trace"]), 6)
        self.assertTrue(result["findings"])
        self.assertTrue(all(f["sources"] and f["evidence_sufficient"] for f in result["findings"]))
        self.assertIn("**Fact:**", result["report_markdown"])
        self.assertIn("**Inference:**", result["report_markdown"])
        self.assertIn("**Recommendation:**", result["report_markdown"])

    def test_answered_rfi_does_not_become_open_finding(self):
        result = self.agent.investigate("Check answered RFI-021 status")
        self.assertEqual(result["findings"], [])

    def test_sources_point_to_valid_document_lines(self):
        result = self.agent.investigate("Find open fire-stop inspection nonconformance")
        self.assertIn("RISK-NCR-008", [f["id"] for f in result["findings"]])
        for finding in result["findings"]:
            for source in finding["sources"]:
                document = self.agent.docs[source["document_id"]]
                self.assertGreater(source["line"], 0)
                self.assertLessEqual(source["line"], len(document["text"].splitlines()))

    def test_evaluation_records_metrics_and_limitations(self):
        result = evaluate(ROOT / "data" / "evaluation.json", ROOT / "data" / "project.json")
        self.assertEqual(result["cases"], 10)
        self.assertIn("micro_f1", result)
        self.assertTrue(result["limitations"])


if __name__ == "__main__":
    unittest.main()
