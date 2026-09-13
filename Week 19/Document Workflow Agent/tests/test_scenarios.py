from scripts.scenarios import BASE_DRAWING, SCENARIOS
from tests.support import ServiceTest


class ScenarioTests(ServiceTest):
    def setUp(self):
        super().setUp()
        self.service.tools.index_document(self.doc(BASE_DRAWING, "previous.txt"))


def scenario_test(scenario):
    def check(self):
        run = self.service.agent.run(self.doc(scenario["text"]), scenario["task"])
        self.assertEqual(run["status"], "completed", run["result"])
        result = run["result"]
        output = result["outputs"]
        self.assertEqual(len(result["tools_used"]), len(set(result["tools_used"])))
        self.assertEqual(result["stop_reason"], "goal_satisfied")
        self.assertEqual(run["events"][-1]["kind"], "run_finished")
        self.assertTrue(all(e["reason"] for e in run["events"] if e["kind"] == "decision"))
        if "action" in scenario:
            self.assertEqual(output["recommend_next_action"]["action"], scenario["action"])
            self.assertFalse(output["recommend_next_action"]["external_action_executed"])
        if "revision" in scenario:
            self.assertEqual(output["detect_previous_revisions"]["status"], scenario["revision"])
        if "tool_count" in scenario:
            self.assertEqual(len(result["tools_used"]), scenario["tool_count"])
        if "type" in scenario:
            self.assertEqual(output["classify_document"]["document_type"], scenario["type"])
    check.__doc__ = scenario["description"]
    return check


for scenario in SCENARIOS:
    setattr(ScenarioTests, "test_" + scenario["id"], scenario_test(scenario))
