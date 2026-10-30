from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.agent import ProjectAgent  # noqa: E402
from app.server import serve  # noqa: E402
from app.evaluation import evaluate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 25 Project Intelligence Agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Run the packaged management investigation")
    investigate = sub.add_parser("investigate", help="Investigate a custom request")
    investigate.add_argument("request", nargs="+", help="Request text")
    sub.add_parser("evaluate", help="Run the labeled evaluation set")
    sub.add_parser("test", help="Run unit and integration tests")
    sub.add_parser("serve", help="Start the local HTTP API")
    args = parser.parse_args()

    if args.command == "serve":
        serve()
        return 0
    if args.command == "test":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if args.command == "evaluate":
        result = evaluate(ROOT / "data" / "evaluation.json", ROOT / "data" / "project.json")
        out = ROOT / "outputs" / "evaluation_results.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0

    request = (
        "Analyze this project and identify major outstanding issues, risks, overdue actions, "
        "and items requiring management attention."
        if args.command == "demo" else " ".join(args.request)
    )
    result = ProjectAgent(ROOT / "data" / "project.json").investigate(request)
    outputs = ROOT / "outputs"
    outputs.mkdir(exist_ok=True)
    (outputs / "latest_report.md").write_text(result["report_markdown"], encoding="utf-8")
    (outputs / "latest_trace.json").write_text(json.dumps(result["trace"], indent=2), encoding="utf-8")
    print(result["report_markdown"])
    print(f"\nTrace: {outputs / 'latest_trace.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
