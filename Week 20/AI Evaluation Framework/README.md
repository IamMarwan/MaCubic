# Week 20 — AI Evaluation Framework

A standalone, reproducible framework for comparing document-AI configurations using a versioned benchmark, explicit scoring rules, SQLite history, and a self-contained HTML dashboard.

**Included evidence is measured local execution.** Two distinct statistical model pipelines and two controlled ablations were run. The local models are TF-IDF centroid and multinomial Naive Bayes classifiers, combined with TF-IDF/BM25 retrieval and extractive rules. They are not commercial LLMs. OpenAI model/prompt configurations are included, but **no live API model was run while preparing this package**. API token usage and cost cannot be inferred from local timings.

## Assignment coverage

| Deliverable | Included implementation |
|---|---|
| Automated evaluation framework | `evalkit/`, `run.py`, CLI and quality gate |
| Realistic benchmark with expected answers | 105 fictional construction scenarios, 30 source documents, source-line annotations |
| Model / prompt comparison | Four executed local configurations; three live model/prompt templates; prediction replay |
| Required metrics | Retrieval, answers, citations, unsupported claims, metadata, classification, latency, tokens and estimated cost |
| Historical results | Append-only run IDs, SQLite case checkpoints, JSON run exports |
| Dashboard / report | Offline HTML dashboard with selectors, comparison, failures, source text, history and CSV export |
| At least two configurations compared | `baseline`, `candidate`, `retrieval_only`, `policy_only` |
| Methodology | `docs/methodology.md`, dataset card, integration guide, validation evidence |

## 1. Extract and open in VS Code

The archive contains `Week 20/AI Evaluation Framework/`. Extract it directly into your existing MaCubic repository root. Add no extra `Week 20` folder around those contents.

Example destination, matching the Week 19 setup:

`C:\Users\Dell\Desktop\MaCubic\Week 20\AI Evaluation Framework`

If your repository is elsewhere, substitute its actual path. The archive contains Week 20 only.

## 2. Create the environment and install

Python **3.11 or newer**. The runtime and tests need no external packages; `requirements.txt` documents this deliberately.

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\Week 20\AI Evaluation Framework"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell activation is restricted, use `.\.venv\Scripts\python.exe` in place of `python`; changing your machine's execution policy is unnecessary. On macOS/Linux, activate with `source .venv/bin/activate`.

## 3. Validate and test

```powershell
python run.py validate
python scripts/run_tests.py
```

The test runner writes `outputs/test_report.json`. Tests check scoring against hand-calculated examples, schema validation, provider failures, no gold-answer leakage through the provider interface, comparison compatibility, persistence, precomputed vectors and external prediction replay.

## 4. Run the full local demonstration

```powershell
python run.py demo
python run.py serve
```

Open [the local dashboard](http://127.0.0.1:8000/comparison.html). Keep that terminal running; stop it with Ctrl+C. You can also open `outputs/comparison.html` directly in a browser without a server.

The demo evaluates four configurations on the **same 70 test cases**. It creates:

- `outputs/history.sqlite3` — run manifests, case results and summaries.
- `outputs/runs/<run_id>.json` — complete inspectable evidence.
- `outputs/comparison.html` — self-contained dashboard.
- `outputs/summary.csv` — numeric metrics, with blank cells for unavailable values.
- `outputs/paired_comparisons.json` — exploratory paired bootstrap differences.

The 35 development cases are available with `--split dev`. Split is part of the comparison identity. Runtime outputs are gitignored; the verified submission snapshots are in `docs/evidence/`.

### Demo flow for a reviewer

1. Compare `baseline` with `candidate` in the dashboard.
2. Inspect answer correctness and metadata accuracy together with citation coverage.
3. Select **Failures only** and inspect a missed document or absent answer.
4. Compare `baseline` with `retrieval_only`: the retrieval component is the only change.
5. Compare `baseline` with `policy_only`: only extraction label handling changes.
6. Inspect the provenance and rerun the demo to show an additional historical run.

See `docs/results.md` for the actual packaged results and their limits.

## 5. Run one configuration or check a regression gate

```powershell
python run.py run --config configs/candidate.json
python scripts/ci_check.py
python run.py history
```

The quality gate uses `configs/quality_gate.json` and returns a nonzero exit code on missing metrics, insufficient cases, execution errors or a failed threshold. These thresholds are assignment demonstration targets, not approved company standards.

To generate an exploratory paired comparison, substitute two actual JSON filenames printed in `outputs/runs/`:

```powershell
python run.py compare "outputs/runs/BASELINE_RUN.json" "outputs/runs/CANDIDATE_RUN.json" --metric answer_correctness
```

The comparator refuses different datasets, samples, splits, metric versions, code versions or evidence types. A retrieval comparison also requires the same `top_k`.

## 6. Compare real LLM models and prompts

No API calls happen in the default demo. To run a live comparison, set credentials and model IDs locally. Use model identifiers available to your account that support Responses structured JSON output. **Do not paste your key into chat or commit it.** `.env.example` is a reference; this project reads environment variables and does not automatically load `.env`.

```powershell
$env:OPENAI_API_KEY = Read-Host "OpenAI API key" -MaskInput
$env:EVAL_MODEL_A = "YOUR_MODEL_A_ID"
$env:EVAL_MODEL_B = "YOUR_MODEL_B_ID"
```

`-MaskInput` requires PowerShell 7.1+. In Windows PowerShell 5.1, use:

```powershell
$key = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $key).Password
```

Enter the applicable current input, cached-input and output prices per million tokens in the three `configs/llm_*.json` files, along with their source URL and verification date. Prices are deliberately **null** initially. Unknown pricing is shown as N/A, never zero or a guessed price.

Start with a small development smoke run:

```powershell
python run.py run --config configs/llm_a_grounded.json --split dev --limit 3
```

Then run the same full test split for all configurations:

```powershell
python run.py run --config configs/llm_a_baseline.json
python run.py run --config configs/llm_a_grounded.json
python run.py run --config configs/llm_b_grounded.json
python run.py report
python run.py serve
```

These commands make billed API requests. Compare A/baseline with A/grounded for the prompt experiment; compare A/grounded with B/grounded for the model experiment. Keep retrieval, case sample and pricing assumptions consistent. API timeouts and incomplete responses are recorded as failures; there is no silent offline fallback or automatic retry. Failed requests can still incur costs; missing usage remains unknown.

The adapter uses the [official Structured Outputs format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). The package supports structured document QA, not unrestricted prose grading. Local extraction policies and live LLM prompts are separate mechanisms.

## 7. Compare embedding models or previous training projects

Use `python run.py export-inputs` to export source documents and public task inputs without answer keys. The `vectors` retriever accepts precomputed document/query embeddings with corpus and question hashes. It supports any embedding provider that can produce the documented numeric vector format. The `replay` provider scores previously collected predictions, retrieved IDs, usage and latency. See `docs/integrations.md` for concrete schemas and commands.

Embedding generation is external to the vector-scoring runner. Its latency, tokens and charges must be measured separately; they are excluded from the report's per-response metrics. Imported prediction timing/usage is labeled unverified.

## 8. Review file groups

Read `docs/file_batches.md` for the same grouped review flow as Week 19. The complete package is already present; manual creation of each file is unnecessary.

## 9. Commit Week 20 only

After your local tests and demo, use your confirmed repository root:

```powershell
cd "C:\Users\Dell\Desktop\MaCubic"
git remote -v
git status --short
git add "Week 20/AI Evaluation Framework"
git diff --cached --stat
git commit -m "Add Week 20 AI evaluation and benchmarking framework"
git push origin main
```

Check that the staged diff contains only the intended Week 20 files. The package itself does not run Git commands, push changes or send email. If Git reports a conflict or rejects a push, inspect it before proceeding; do not force-push.

After verification and upload, use `docs/submission_email.md`.
