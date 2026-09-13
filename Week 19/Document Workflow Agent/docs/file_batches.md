# Larger file batches for review in VS Code

The complete files are already supplied. Use these groups to inspect the
implementation without moving through one file per message.

| Batch | Files | What to inspect |
|---|---|---|
| 1 — Foundation | `app/config.py`, `app/models.py`, `app/ingestion.py`, `app/repository.py`, `.env.example`, `requirements.txt` | Settings, input validation, state and database |
| 2 — Agent | `app/tools.py`, `app/policy.py`, `app/planner.py`, `app/agent.py` | Eight tools, dynamic prerequisites and the decision loop |
| 3 — API and demo | `app/server.py`, `run.py`, `web/index.html`, `web/app.js`, `web/style.css`, `web/api.html` | Uploads, task API, history and dashboard |
| 4 — Scenarios and tests | `scripts/scenarios.py`, `scripts/generate_samples.py`, `scripts/demo_client.py`, `scripts/run_tests.py`, `tests/` | Realistic cases, test coverage and live demonstration |
| 5 — Submission | `README.md`, `docs/`, `Dockerfile`, `.gitignore`, `.dockerignore` | Setup, architecture, verification evidence and submission |

Implementation order: extract folders → open files in VS Code → create the
environment → install requirements → run tests → start the API → run the demo
→ configure and demonstrate model mode → commit/push → send the email.
