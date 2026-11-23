# AI Tender Analysis and Bid Comparison

Week 2 extends the Week 1 tender register in the same standalone prototype. It compares three synthetic bids against the same 30 stable requirement IDs, records source-linked compliance decisions, surfaces qualifications and deviations, and exports clarification questions.

## Project structure

- `app/`: FastAPI service, evidence/status analysis, and browser comparison workspace.
- `fixtures/development/`: 30-requirement tender, amendment, BOQ, the three Week 1 bid workbooks, plus split technical/commercial/delivery bid PDFs and irrelevant catalog attachments.
- `fixtures/week4_reserved/`: frozen 10-requirement / 10-line BOQ / two-bid package. Week 2 generation, analysis, and evaluation do not read it.
- `annotations/labeled_90_pairs.csv`: reference status for all 30 requirements × 3 bidders, rationale, and unresolved question.
- `annotations/working_matrix.json`: all pair decisions, tender citation, bidder passages, source locations, searched files, flags, and clarification.
- `annotations/deviation_register.json` and `annotations/clarification_questions.csv`: surfaced qualifications and bidder-specific question export.
- `annotations/evaluation_report.md` and `.json`: exact status agreement, per-status metrics, confusion matrix, and adversarial checks.
- `annotations/week1/`: preserved Week 1 reference and evaluation files.
- `schemas/`: JSON Schemas for the requirement and matrix records.
- `docs/status_rules.md` and `docs/demo_script.md`: status policy and five-minute walkthrough.

## Run on Windows

From the repository root:

```powershell
cd "Week 2/AI Tender Analysis and Bid Comparison"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_week2_fixtures.py
python scripts\evaluate.py
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Filter the 90 requirement-bid rows by bidder, category, status, or mandatory gaps. Click a tender or bid source link to inspect the searchable PDF. API documentation is at <http://127.0.0.1:8000/docs>.

On macOS/Linux, activate the environment using `source .venv/bin/activate`.

## Analysis approach

The prototype prefers stable requirement IDs when present. It can also map untagged passages with normalized token overlap, curated terminology synonyms, and fuzzy phrase similarity. Status rules are intentionally conservative: explicit positive commitment is needed for **met**; an explicit limitation is **partially met**; a refusal or exclusion is **not met**; absent or contradictory evidence is **not evidenced**; and **not applicable** requires a documented scope reason. Each pair retains the tender reference, bid quotation or searched-file list, rationale, and question.

Seeded signals include an explicit exclusion, a delivery-time deviation, an alternative proposal, a warranty evidence gap, and contradictory bid statements. Mandatory gaps are called out separately. The Week 4 reserved fixture is not loaded or used by the Week 2 evaluator.

## Evaluation

Run `python scripts/evaluate.py` to regenerate the matrix, clarification CSV, deviation register, and evaluation reports. The development result is **90/90 exact status agreement (100%)** on this controlled synthetic fixture. The report publishes per-status precision/recall/F1, the confusion matrix, and ID-free paraphrase / contradiction / omission / irrelevant-attachment checks. This score describes this fixed synthetic package and does not predict accuracy on real, unstructured bids.

## Standalone scope

The service uses local files and SQLite for the inherited Week 1 register. It requires no Arkan code, databases, APIs, credentials, or deployment access. The Week 2 matrix is generated from the included development fixtures. It is a transparent deterministic prototype, not an autonomous procurement decision system.
