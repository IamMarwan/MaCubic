# Week 25 — Project Intelligence Agent

A standalone, evidence-first agent that investigates a fictional construction project and produces a management report. The agent plans a multi-step investigation, searches and follows document links, records each tool call, flags disagreements, and cites source documents for each finding.

**Evidence scope:** the included demonstration runs against a simulated dataset with deterministic local tools. The package makes no live LLM calls. Dates, project records, and evaluation results are fictional and generated for this assignment.

## Assignment coverage

| Deliverable | Included |
|---|---|
| Working Project Intelligence Agent | `app/` CLI and local HTTP API |
| Realistic simulated project dataset | 12 linked contract, RFI, submittal, minutes, inspection, progress, correspondence, and schedule records in `data/project.json` |
| Multi-step orchestration | request understanding → plan → search → follow links → gather evidence → assess → report |
| Evidence and citation engine | document IDs, line ranges, quotes, and source titles on each finding |
| Complete execution trace | JSONL trace for every demo investigation under `examples/` |
| Evaluation dataset/results | 10 labeled scenarios, deterministic evaluator, measured result in `outputs/evaluation_results.json` |
| Architecture and technical documentation | `docs/` |
| 15-minute demonstration | timed walkthrough and commands in `docs/DEMO_SCRIPT.md` |

The system separates **Fact**, **Inference**, and **Recommendation**. The sample engine only emits findings linked to dataset evidence. When it finds contradictory records, it reports the conflict and leaves resolution to a human reviewer. It never issues instructions, changes project records, or contacts people.

## Requirements and setup

Python 3.11 or newer. Runtime and tests use only the Python standard library.

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\Week 25\Project Intelligence Agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is restricted, run `.\.venv\Scripts\python.exe` directly. On macOS/Linux, activate with `source .venv/bin/activate`.

## Run the demonstration

```powershell
python run.py demo
```

This writes a Markdown report and complete JSON trace to `outputs/`. The packaged copies in `examples/` are reproducible sample evidence from the same deterministic run.

Run one custom investigation:

```powershell
python run.py investigate "Identify overdue actions, unresolved RFIs and submittals, and schedule risks"
```

The report is printed and saved as `outputs/latest_report.md`; its trace is saved as `outputs/latest_trace.json`.

## Run the API

```powershell
python run.py serve
```

The local API listens on `127.0.0.1:8080`. `POST /investigate` accepts JSON such as:

```json
{"request":"Analyze the project and list major risks and overdue actions"}
```

The response contains the report and execution trace. `GET /health` returns service status. Optional bearer-token authentication can be enabled with `PROJECT_AGENT_TOKEN`; see `docs/SECURITY.md`.

## Evaluate and test

```powershell
python run.py evaluate
python run.py test
```

The evaluator compares detected finding IDs with the labeled cases and reports precision, recall, F1, citation coverage, and scenario accuracy. These are measured only against the included synthetic evaluation set; they do not establish performance on real project records.

## Repository placement and upload

The ZIP contains `Week 25/Project Intelligence Agent/`. Extract it into the root of the existing MaCubic repository so the final path is `MaCubic\Week 25\Project Intelligence Agent`.

```powershell
Set-Location "C:\Users\Dell\Desktop\MaCubic"
Expand-Archive -Path "$HOME\Downloads\Week_25_Project_Intelligence_Agent.zip" -DestinationPath "." -Force
git status --short
git add "Week 25/Project Intelligence Agent"
git diff --cached --stat
git commit -m "Add Week 25 Project Intelligence Agent"
git push origin main
```

Review the staged paths before committing. The archive does not run Git commands or push changes.

## Project map

```text
app/              orchestration, evidence tools, report builder, and HTTP API
data/             fictional linked project and evaluation scenarios
docs/             architecture, data, evaluation, security, and demo notes
examples/          sample report and complete execution trace
outputs/           generated reports, traces, and evaluation results
tests/             standard-library unit and integration checks
scripts/           evaluation entry point
```
