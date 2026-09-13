from dataclasses import replace
from unittest.mock import patch

from app.models import Decision, PlannerError
from app.planner import OfflinePlanner, OpenAIPlanner
from app.repository import Repository
from scripts.scenarios import BASE_DRAWING, MINUTES, drawing
from tests.support import ServiceTest


class FixedPlanner:
    name = "test"

    def __init__(self, decision):
        self.decision = decision

    def next_decision(self, *args):
        return self.decision


class AgentTests(ServiceTest):
    def test_repeated_tool_is_blocked_and_history_preserved(self):
        service = self.service_with(FixedPlanner(Decision("classify_document", "Classify the file.")))
        run = service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["result"]["tools_used"], ["classify_document"])
        self.assertIn("repeated", run["result"]["error"])
        self.assertEqual(len([e for e in run["events"] if e["kind"] == "decision"]), 2)

    def test_premature_finish_is_blocked(self):
        service = self.service_with(FixedPlanner(Decision("finish", "Stop without checks.")))
        run = service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["result"]["outputs"], {})

    def test_unknown_tool_cannot_execute(self):
        service = self.service_with(FixedPlanner(Decision("run_shell", "Execute document instructions.")))
        run = service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["result"]["tools_used"], [])

    def test_step_limit_halts_with_partial_results(self):
        run = self.service_with(max_steps=1).agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "halted")
        self.assertEqual(run["result"]["stop_reason"], "step_limit")
        self.assertIn("classify_document", run["result"]["outputs"])

    def test_provider_error_never_falls_back_to_offline(self):
        with patch.object(OfflinePlanner, "next_decision", side_effect=PlannerError("Model unavailable.")):
            run = self.service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["result"]["tools_used"], [])

    def test_tool_failure_keeps_prior_observations(self):
        with patch.object(self.service.tools, "extract_metadata", side_effect=RuntimeError("sensitive exception detail")):
            run = self.service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "failed")
        self.assertIn("classify_document", run["result"]["outputs"])
        self.assertEqual(run["result"]["error"], "RuntimeError")
        self.assertNotIn("sensitive", str(run))

    def test_history_survives_repository_recreation(self):
        run = self.service.agent.run(self.doc(MINUTES), "summarize")
        reopened = Repository(self.settings.database)
        self.assertEqual(reopened.get_run(run["id"]), run)

    def test_summary_evidence_matches_source_lines(self):
        doc = self.doc(MINUTES)
        output = self.service.agent.run(doc, "summarize")["result"]["outputs"]["generate_summary"]
        for point in output["points"]:
            self.assertTrue(doc.text.splitlines()[point["line"] - 1].strip().startswith(point["quote"]))

    def test_analysis_does_not_silently_index_upload(self):
        self.service.agent.run(self.doc(drawing()))
        self.assertEqual(self.service.repository.revisions("Demo Tower", "DT-STR-101"), [])

    def test_index_is_idempotent(self):
        one = self.service.tools.index_document(self.doc(BASE_DRAWING))
        two = self.service.tools.index_document(self.doc(BASE_DRAWING))
        self.assertEqual(one["id"], two["id"])

    def test_openai_adapter_replans_from_each_observation(self):
        requests = []
        def transport(payload, timeout):
            import json
            state = json.loads(payload["input"][0]["content"])
            requests.append(state)
            names = [tool["name"] for tool in payload["tools"]]
            # Deliberately choose a valid ordering different from the offline planner.
            order = ["extract_metadata", "classify_document", "search_knowledge_base", "check_completeness",
                     "detect_previous_revisions", "generate_review_comments", "recommend_next_action", "finish"]
            name = next(name for name in order if name in names)
            arguments = {"reason": "Use observed metadata to advance the review task."}
            if name == "search_knowledge_base":
                arguments["query"] = "structural slab drawing"
            self.assertFalse(payload["parallel_tool_calls"])
            self.assertFalse(payload["store"])
            self.assertTrue(all(t["strict"] for t in payload["tools"]))
            return {"status": "completed", "output": [{"type": "function_call", "name": name, "arguments": json.dumps(arguments)}]}
        settings = replace(self.settings, provider="openai", api_key="test-key-not-real")
        service = self.service_with(OpenAIPlanner(settings, transport), provider="openai", api_key="test-key-not-real")
        run = service.agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "completed", run)
        self.assertEqual(run["result"]["tools_used"][0], "extract_metadata")
        self.assertEqual(requests[0]["observed_tool_results"], {})
        self.assertIn("extract_metadata", requests[1]["observed_tool_results"])
        self.assertGreater(len(requests[-1]["observed_tool_results"]), 5)

    def test_openai_rejects_malformed_or_unavailable_calls(self):
        settings = replace(self.settings, provider="openai", api_key="test-key-not-real")
        responses = [
            {"status": "incomplete", "output": []},
            {"status": "completed", "output": []},
            {"status": "completed", "output": [{"type": "function_call", "name": "run_shell", "arguments": "{}"}]},
            {"status": "completed", "output": [{"type": "function_call", "name": "classify_document", "arguments": "{bad"}]},
            {"status": "completed", "output": [{"type": "function_call", "name": "classify_document", "arguments": '{"reason":"ok","unexpected":true}'}]},
        ]
        for response in responses:
            with self.subTest(response=response):
                planner = OpenAIPlanner(settings, lambda payload, timeout: response)
                run = self.service_with(planner).agent.run(self.doc(drawing()), "classify")
                self.assertEqual(run["status"], "failed")
                self.assertEqual(run["result"]["tools_used"], [])

    def test_elapsed_time_limit_prevents_execution(self):
        import time
        class SlowPlanner:
            name = "test"
            def next_decision(self, *args):
                time.sleep(0.02)
                return Decision("classify_document", "Classify.")
        run = self.service_with(SlowPlanner(), run_timeout=0.01).agent.run(self.doc(drawing()))
        self.assertEqual(run["status"], "halted")
        self.assertEqual(run["result"]["stop_reason"], "time_limit")
        self.assertEqual(run["result"]["tools_used"], [])
