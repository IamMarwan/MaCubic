# Enterprise AI Workflow Platform (Weeks 21–24)

A compact demonstration project combining the four assignments: an AI gateway with configurable routing, an MCP document server, human approval workflows, and defensive AI application security.

## Features

- Unified FastAPI endpoint with configurable model/provider catalog, task-based routing, evaluation scorecard, retries, fallback, usage/token/cost tracking, bearer-key auth, and in-memory per-key rate limiting.
- Eight MCP tools backed by a configurable JSON document dataset: search, metadata, content, knowledge search, revision comparison, related documents, validation, and summary.
- Human review queue with configurable confidence bands and mandatory approval for high-risk actions; reviewers can approve, reject, or modify; SQLite audit events record requests and decisions.
- Role and document-level access checks, tool permissions, bounded input validation, prompt-injection signals, output schema validation, audit logging, and a 25-case adversarial suite.
- Docker deployment, OpenAPI docs, architecture and security notes, demonstration client, and 10 end-to-end scenario descriptions.

## Quick start (Windows PowerShell)

```powershell
cd "Week 21-24\Enterprise AI Workflow Platform"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Demo credentials are `demo-app-key` and `demo-reviewer-key`; they are for local demonstration only. Set `APP_KEYS_JSON` to your own credentials before sharing or deploying. The app stores its SQLite database at `data/workflow.db` by default.

## Demo

In another PowerShell terminal:

```powershell
cd "Week 21-24\Enterprise AI Workflow Platform"
.\.venv\Scripts\Activate.ps1
python scripts/demo.py
```

The script submits a document classification, demonstrates reviewer modification/approval, reads the audit log, and sends an AI gateway request. It also submits DOC-102 to demonstrate high-confidence automatic processing. Run `python scripts/mcp_demo_client.py` to connect an MCP-compatible client over stdio, list tools, and call document search. Set `MCP_USER_ID` / `MCP_ROLE` as needed.

## API outline

All `/v1/*` routes use `X-API-Key`.

- `POST /v1/gateway/chat` — route by `task_type`, return result and usage metadata.
- `POST /v1/workflows` — submit a task/document; returns automatic result or pending approval.
- `GET /v1/approvals` — reviewer queue.
- `POST /v1/approvals/{id}/decision` — reviewer decision: `approve`, `reject`, or `modify` (modified action required).
- `GET /v1/audit` — user's audit events; reviewer sees all events.
- `GET /v1/usage` — estimated token counts, estimated cost, latency, model, and fallback records; reviewer sees all users.
- `GET /v1/documents/search?q=...` — search only documents visible to the caller.
- `GET /health` — liveness endpoint.

## Configuration

- `configs/models.json`: provider endpoint/model, enablement, price per 1K tokens, timeout, retries, and fallback order. Provider secrets are read from environment variables named by `api_key_env`.
- `configs/routing.json`: task-specific candidate models and minimum quality / maximum cost / latency limits, plus scoring weights.
- `configs/evaluation_results.json`: **illustrative sample scorecard**, not the user's Week 3 results. Replace it with the actual evaluation measurements before claiming the route scores reflect Week 3.
- `configs/security.json`: confidence thresholds, risk actions, maximum input size, rate limit, and prompt-injection signal phrases.
- `data/documents.json`: demo records and revision content. Add/update records here; the service loads this file rather than embedding business documents in code.

Token counts are estimated from whitespace-separated words, and cost is estimated from those counts and configured prices. The scorecard uses quality, cost, and latency to rank eligible candidates. If measured quality is below the configured floor or the candidate exceeds a cost/latency cap, routing skips it. Fallback proceeds to the next eligible configured model.

## MCP

Install requirements, then run `python mcp_server.py`. The process exposes eight schemas/tools through the MCP stdio transport. MCP stdio is intended to run as a locally authenticated process; its identity is selected by `MCP_USER_ID` and `MCP_ROLE`. Tool functions still apply document ownership and role checks. For remote multi-user deployment, put the MCP transport behind an authenticated host/proxy and map verified identity claims into those values.

## Docker

```powershell
docker compose up --build
```

The API listens on port 8000. The SQLite file and dataset are mounted in the project directory. Change demo keys through `APP_KEYS_JSON` in `.env` before deployment.

## Tests and demonstration scenarios

Run `pytest -q` for 13 workflow/API tests, 25 adversarial input/security cases, and one validation test. The suite uses the local mock provider and temporary SQLite files. `docs/DEMO_SCENARIOS.md` lists the 10 human-review and MCP demonstration scenarios. `docs/SECURITY_RESULTS.md` records the adversarial cases and their execution results.

## Limitations

This is an educational, single-process reference implementation. Rate limits are in-memory, SQLite is for local demonstration, prompt-injection detection is heuristic and cannot guarantee detection, and the bundled model metrics are sample values. Production deployment should use a managed identity provider, persistent distributed rate limiting, encrypted/managed database, key rotation, monitoring, and a reviewed model evaluation dataset.
