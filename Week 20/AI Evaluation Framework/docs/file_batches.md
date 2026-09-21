# Week 20 file review flow

All files are supplied together. Open the project in VS Code and inspect these groups.

| Batch | Files | Purpose |
|---|---|---|
| 1 — Benchmark and contract | `data/`, `scripts/build_dataset.py`, `evalkit/common.py` | Sources, expected answers, splits, training data and input boundary |
| 2 — Models and retrieval | `evalkit/retrieval.py`, `evalkit/classifiers.py`, `evalkit/providers.py`, `configs/`, `prompts/` | Local pipelines, live model/prompt adapters and integrations |
| 3 — Evaluation and history | `evalkit/metrics.py`, `evalkit/runner.py`, `evalkit/storage.py`, `evalkit/gates.py` | Measurements, denominators, evidence and regression checks |
| 4 — Report and verification | `evalkit/report.py`, `web/report.html`, `tests/`, `scripts/run_tests.py`, `scripts/ci_check.py` | Dashboard, CSV and meaningful validation |
| 5 — Delivery | `README.md`, `docs/`, `requirements.txt`, `.gitignore`, `.env.example` | Installation, methodology, measured results and submission |

Implementation order: extract folders → open in VS Code → create environment → install requirements → validate data → run tests → run demo → inspect dashboard → optionally compare live models → commit/push Week 20 → send completion email.
