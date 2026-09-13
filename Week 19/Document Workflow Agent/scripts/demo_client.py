"""Live HTTP demonstration; the API must be running in another terminal."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from scripts.scenarios import BASE_DRAWING, SCENARIOS


def request(base_url, path, payload=None):
    req = urllib.request.Request(base_url.rstrip("/") + path,
                                 data=json.dumps(payload).encode("utf-8") if payload else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode('utf-8')}") from None
    except urllib.error.URLError:
        raise RuntimeError("Cannot reach the API. Start python run.py in another terminal.") from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--all", action="store_true", help="Run all 17 scenarios instead of the three-case live demo.")
    parser.add_argument("--assert-expected", action="store_true", help="Check expected outcomes; useful for offline regression testing.")
    args = parser.parse_args()
    health = request(args.base_url, "/api/v1/health")
    print(f"Document Workflow Agent | provider={health['provider']} | model={health.get('model')}")
    request(args.base_url, "/api/v1/documents/index", {"filename": "previous_drawing_rev01.txt", "text": BASE_DRAWING})
    selected = SCENARIOS if args.all else [SCENARIOS[0], SCENARIOS[1], SCENARIOS[8]]
    results = []
    failures = []
    for scenario in selected:
        run = request(args.base_url, "/api/v1/runs", {"filename": f"{scenario['id']}.txt",
                       "text": scenario["text"], "task": scenario["task"]})
        results.append(run)
        result = run["result"]
        print(f"\n{scenario['id']} | {run['status']} | {len(result['tools_used'])}/8 tools")
        for event in run["events"]:
            if event["kind"] == "decision":
                print(f"  {event['step']:02d} {event['tool']}: {event['reason']}")
        output = result["outputs"]
        if "recommend_next_action" in output:
            print("  NEXT ACTION:", output["recommend_next_action"]["action"])
        print("  SKIPPED:", ", ".join(result["tools_skipped"]) or "none")
        if run["status"] != "completed":
            failures.append(f"{scenario['id']}: {run['status']} ({result['error'] or result['stop_reason']})")
        if args.assert_expected:
            checks = {
                "action": output.get("recommend_next_action", {}).get("action"),
                "revision": output.get("detect_previous_revisions", {}).get("status"),
                "tool_count": len(result["tools_used"]),
                "type": output.get("classify_document", {}).get("document_type"),
            }
            for key, actual in checks.items():
                if key in scenario and actual != scenario[key]:
                    failures.append(f"{scenario['id']}: expected {key}={scenario[key]}, got {actual}")
    folder = ROOT / "outputs"
    folder.mkdir(exist_ok=True)
    path = folder / ("all_scenarios.json" if args.all else "live_demo.json")
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(results)} real HTTP run results to {path}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("All submitted runs completed successfully.")


if __name__ == "__main__":
    main()
