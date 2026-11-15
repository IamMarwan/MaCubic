# AI Tender Analysis and Bid Comparison

A self-contained prototype for extracting a traceable tender requirement register, browsing source evidence, and exporting JSON or CSV. It uses synthetic documents and local storage only. It has no Arkan integration.

## Included packages

- `fixtures/development/`: tender requirements, amendment/conflict examples, 30-line BOQ, and three bidder submissions.
- `fixtures/week4_reserved/`: a separate frozen reference package with 10 requirements, 10 BOQ lines, and two bids. Keep it out of development and tuning.
- `annotations/`: development reference answers, match policy, benchmark evaluator, and evaluation report.
- `app/`: FastAPI ingestion service and a browser register/source viewer.
- `schemas/`: JSON Schema for extracted requirements and register exports.

## Requirements

Python 3.10 or newer.

## Run

```powershell
cd "Week 26/AI Tender Analysis and Bid Comparison"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_fixtures.py
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Use **Load development fixture** to ingest the tender, amendment, BOQ, and bidder files, or upload supported PDF/XLSX files. API documentation is at <http://127.0.0.1:8000/docs>.

On macOS/Linux, activate with `source .venv/bin/activate` and run `python scripts/generate_fixtures.py`.

## Ingestion behavior

The prototype extracts explicitly tagged synthetic requirement rows (`REQ-xx | ...`) from searchable PDF text or spreadsheet cells. It preserves document/page or sheet/cell coordinates. It flags seeded amendment conflicts, applies supersession only when an amendment explicitly says it supersedes an earlier clause, represents absent values as `unknown`, and deduplicates repeat imports by stable requirement ID and normalized content. This is a transparent baseline, not a general-purpose language model or production procurement system.

PDFs must contain an extractable text layer. Scanned/image-only PDFs and unsupported file types produce a clear 400 error. XLSX ingestion records exact sheet and cell coordinates. Uploaded files are stored under `data/uploads/`; the SQLite register is `data/register.db`.

## Evaluate

```powershell
python scripts\evaluate.py
```

Matching uses the stable reference ID and exact normalized requirement text. Precision = matched extracted reference entries / all extracted requirements; recall = matched reference entries / all reference entries. The report also counts duplicate IDs, omissions, wrong values, unsupported inferences, invalid source references, and conflict detection. The benchmark is intentionally deterministic; its results do not establish accuracy on arbitrary tender documents.

## Five-minute demonstration

See [`docs/demo_script.md`](docs/demo_script.md) for a timed walkthrough.

## Deadline note

The assignment email lists the deadline as `16/11/202`, which appears incomplete. This project does not infer or correct the missing year.

## Limitations

- Extraction relies on a documented row format and does not claim to understand arbitrary prose.
- No authentication, multi-user permissions, cloud storage, or external service is included.
- Commercial bid totals are shown as provided in the synthetic bid workbook; the prototype does not calculate award recommendations.
- The reserved Week 4 fixture is packaged for later evaluation and is not used by the development benchmark.
