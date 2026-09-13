"""Run the meaningful test suite and save a reproducible result report."""

import json
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT


if __name__ == "__main__":
    start = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "python": sys.version.split()[0],
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "duration_seconds": round(time.monotonic() - start, 3),
              "successful": result.wasSuccessful(),
              "scope": "Offline policies, actual tool execution, HTTP API, PDF parsing, durable storage and injected OpenAI transport tests. No live model calls."}
    folder = ROOT / "outputs"
    folder.mkdir(exist_ok=True)
    (folder / "test_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
