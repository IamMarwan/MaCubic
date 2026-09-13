# Week 19 — Document Workflow Agent

A standalone document workflow service that selects tools, executes them,
observes the results, and decides what to do next. The project includes a local
HTTP API, browser dashboard, SQLite execution history, eight tools, and 17
fictional construction scenarios.

## What is agentic here?

The orchestrator does not contain a fixed sequence of eight tool calls. On each
step it asks a planner for one action, validates that action, executes the tool,
persists its result, and supplies updated observations to the next decision.
The planner sees only currently eligible tools. Task completion is checked by
the service, not accepted solely because a model says it is finished.

Two planner modes make the behavior transparent:

| Mode | Tool selection | Network/key requirement |
|---|---|---|
| `offline` | Adaptive deterministic policy based on task, document type and metadata | None |
| `openai` | Model chooses one function on each step through the Responses API | Your API key and model access |

**Offline mode is a policy demonstration, not evidence of LLM reasoning.** The
eight tools themselves use deterministic extraction, search and validation in
both modes. The model controls tool choice and ordering in `openai` mode.
The submitted text and tool observations are sent to OpenAI only in that mode.
There is no silent fallback from a failed model request to offline mode.

## Deliverables

| Requirement | Implementation |
|---|---|
| Standalone orchestration service | `app/agent.py`, `app/planner.py`, `app/policy.py` |
| Minimum five tools | All eight requested functions in `app/tools.py` |
| Execution history and logging | SQLite runs and ordered events in `app/repository.py` |
| API for document/task submission | `app/server.py`, `/docs`, `docs/openapi.json` |
| At least ten realistic scenarios | 17 sample documents and scenario tests |
| Architecture diagram | [docs/architecture.md](docs/architecture.md) |
| Live demonstration | Browser dashboard and `scripts/demo_client.py` |

## Tools

| Tool | Result |
|---|---|
| `classify_document` | Document type and matching heading evidence |
| `extract_metadata` | Labelled fields, source lines and conflicting values |
| `search_knowledge_base` | Type-filtered reference matches with IDs and text |
| `check_completeness` | Missing, conflicting and invalid metadata fields |
| `detect_previous_revisions` | Older/newer revisions, duplicate/conflict status and text diff |
| `generate_summary` | Extractive summary with source line references |
| `generate_review_comments` | Comments derived from actual check results |
| `recommend_next_action` | Suggested document-control action and its basis |

`finish` is a planner control action, not an additional document tool.

## Setup — Windows PowerShell

Place this folder at:

`C:\Users\Dell\Desktop\MaCubic\Week 19\Document Workflow Agent`

The downloadable archive already contains `Week 19/Document Workflow Agent/`.
Extract it into your `MaCubic` repository root once; do not add an extra Week 19
folder around the archive contents.

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\Week 19\Document Workflow Agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/run_tests.py
python run.py
```

Use Python 3.11 or 3.12. Validation supplied with this project was run on Python
3.12.14. `pypdf` is the only external runtime dependency; TXT/Markdown processing,
the API, SQLite and the test runner use Python's standard library. Tests use
`unittest`, so installing pytest is unnecessary.

Open the dashboard at [http://127.0.0.1:8000](http://127.0.0.1:8000).
API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

On macOS/Linux, use `source .venv/bin/activate` after creating the environment.

## Live demo — second terminal

Keep the API running in the first terminal. In a second PowerShell terminal:

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\Week 19\Document Workflow Agent"
.\.venv\Scripts\Activate.ps1
python scripts/demo_client.py
```

The client explicitly indexes a previous drawing revision, then submits:

1. A complete new drawing revision: route for human review.
2. A drawing missing its checker: return for completion.
3. Meeting minutes requested as a summary: execute only `generate_summary`.

Every actual decision and tool used is printed. Full responses are saved to
`outputs/live_demo.json`. Refresh the dashboard history to inspect each run.

Run all 17 offline scenarios with expected-outcome assertions:

```powershell
python scripts/demo_client.py --all --assert-expected
```

This writes `outputs/all_scenarios.json`. Do not use exact offline expectations
as an LLM accuracy claim; real model tool order and optional tool use may vary.

## Run the real model planner

Edit `.env`:

```dotenv
AGENT_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=YOUR_REAL_API_KEY
```

Restart the API with `python run.py`, then run `python scripts/demo_client.py`.
The dashboard and every run response identify `openai` and the configured model.
Your account must have access to the selected model. API usage is billed by the
provider. Environment variables set in the terminal override `.env` values.

The adapter uses strict function schemas and one function call per response,
following the [official function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).
The configured model's supported features are documented in the
[GPT-4.1 mini model reference](https://developers.openai.com/api/docs/models/gpt-4.1-mini).

**Verification boundary:** the bundled evidence covers offline execution and
injected model-transport tests. A live OpenAI run was not performed while
preparing this package because no API key was available. Run this mode before
presenting the project as a live model-driven agent.

## Task-specific behavior

| Task | Required outputs | Typical offline tool count |
|---|---|---:|
| `classify` | Classification | 1 |
| `summarize` | Summary | 1 |
| `revisions` | Metadata and revision lookup | 2 |
| `review` / `workflow` | Applicable checks, review comments and next action | 5–7 in the bundled scenarios |

For full review/workflow tasks, technical document types trigger a reference
search; known documents with project/number/revision fields trigger register
lookup. Unknown types go to manual triage. Model mode may select other useful
eligible tools, including a summary. Summary-only/classification-only tasks are
intentionally restricted to their task scope. Offline mode does not interpret
free-form instructions as general natural language commands.

## Register and knowledge base

- Prior revisions are explicitly added through `/api/v1/documents/index`.
- A review submission does not automatically become an indexed revision.
- Register lookups are scoped to both project and document number.
- Numeric revisions, letter sequences, and prefix-number sequences are
  ordered within their own scheme. Mixed schemes require manual review.
- Different file content under the same revision label produces a conflict.
- `data/knowledge_base.json` contains fictional training requirements. It is
  not a set of official Cubic policies or external engineering standards.
- Search is lexical, not vector/semantic retrieval. Add real approved reference
  content and domain-specific rules before using it on operational projects.

## API examples

PowerShell JSON submission:

```powershell
$body = @{
    filename = "drawing.txt"
    text = Get-Content "data\samples\01_complete_new_revision.txt" -Raw
    task = "workflow"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/runs" `
    -ContentType "application/json" -Body $body

$result.result.tools_used
$result.result.outputs.recommend_next_action
```

Raw file upload with curl (use `curl.exe` in Windows PowerShell):

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/runs?filename=drawing.txt&task=workflow" `
    -H "Content-Type: text/plain" `
    --data-binary "@data/samples/01_complete_new_revision.txt"
```

For a PDF, send raw bytes with `application/pdf` and a `.pdf` filename, or use
`content_base64` in JSON. Supply exactly one of `text` or `content_base64`.
Multipart form uploads are not supported; the dashboard sends raw file bytes.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service and configured planner mode |
| GET | `/api/v1/tools` | Tool descriptions and prerequisites |
| POST | `/api/v1/runs` | Submit a document and task |
| GET | `/api/v1/runs?limit=25&offset=0` | Paginated history |
| GET | `/api/v1/runs/{id}` | Run status, outputs and events |
| GET | `/api/v1/runs/{id}/events` | Ordered execution events |
| POST | `/api/v1/documents/index` | Add a prior revision to the register |
| GET | `/api/v1/samples` | Fictional training sample inputs |
| GET | `/openapi.json` | OpenAPI 3.1 specification |

Submission is synchronous. HTTP 201 means the run was recorded; inspect its
`status` for `completed`, `failed` or `halted`. A model/tool failure retains
earlier successful results and an error event. Invalid inputs return HTTP 400
before a run is created. Concurrent submissions above two return 429. A run
appears in history while processing, so its recorded events can be inspected.

## Execution log

Each run stores its ID, creation timestamp, document filename/hash, task,
planner mode, status and result. Events record planning options, tool decisions,
brief business reasons, arguments, tool start/result, duration, failures, stop
reason and unexecuted tools. Decision reasons are concise explanations of
actions; they are not private model chain-of-thought.

Every successful tool can execute at most once per run. Prerequisites prevent
premature comments or recommendations, and the task's completion checks prevent
early finish. The default budget is 12 planner decisions, including `finish`.
The run time budget is checked between actions; it is not a hard process-level
CPU or memory limit for PDF parsing or an executing local tool.

## Tests and evidence

```powershell
python scripts/run_tests.py
# Alternative runner, without the JSON report:
python -m unittest discover -s tests -v
```

The suite includes 17 individually reported scenario tests plus checks for
HTTP submission/history, raw/base64 uploads, PDF input, revision ordering,
metadata conflicts, evidence quotes, persistence, bounded runs, duplicate tool
calls, malformed model output and actual model-adapter replanning with an
injected transport. See [docs/verification.md](docs/verification.md).

Regenerate the checked-in training data if needed:

```powershell
python scripts/generate_samples.py
```

## Docker (configuration supplied; container build not verified here)

```powershell
docker build -t document-workflow-agent .
docker run --rm -p 127.0.0.1:8000:8000 -v agent-data:/app/outputs document-workflow-agent
```

For real model mode, pass the key via an environment variable or secret manager.
The service is intended as a local educational prototype. Public deployment
would need authentication, HTTPS and a production HTTP deployment layer; the
bundled standard-library HTTP server is for the standalone assignment/demo.

## Limits that affect the result

- Classification and metadata tools recognize supported English headings and
  labelled fields. Unknown/unstructured layouts may need manual triage.
- Completeness means declared field presence/format. It does not verify an
  attachment exists, authenticate a signature, or establish engineering approval.
- Recommendations do not send messages, change an external system, or approve
  a document. The analysis/search tools execute; the final external action is a
  recommendation for a human reviewer.
- PDF support uses the text layer. Scanned or blank pages, including such pages
  inside a mixed PDF, are rejected so missing text is not silently overlooked.
  This behavior follows the text-layer/OCR distinction explained by
  [pypdf's text-extraction documentation](https://pypdf.readthedocs.io/en/latest/user/extract-text.html).
- Default input limits: 10 MB, 25 PDF pages and 60,000 extracted characters.
- Text diff is line-based and capped at 80 lines, with a truncation flag.
- The synthetic test results do not measure accuracy on real company documents.

## Repository submission

From your confirmed recent repository root:

```powershell
cd "C:\Users\Dell\Desktop\MaCubic"
git status
git add "Week 19/Document Workflow Agent"
git commit -m "Add Week 19 document workflow agent"
git push origin main
```

`.env`, virtual environments, databases and runtime outputs are ignored.
The fictional verification snapshots under `docs/evidence/` are intentional
submission evidence. See [docs/submission_email.md](docs/submission_email.md)
for the short email draft to use after your local demonstration and upload.
