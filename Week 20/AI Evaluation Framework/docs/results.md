# Measured results — Week 20

Actual execution on Python 3.12.14. The same 70 test cases were used for every run. No commercial LLM or neural embedding calls were made.

| Metric | Baseline | Retrieval only | Policy only | Candidate |
|---|---:|---:|---:|---:|
| Complete case success | 60.0% | 60.0% | 94.3% | 94.3% |
| Answer correctness | 47.4% | 47.4% | 89.5% | 89.5% |
| Retrieval recall@3 | 91.7% | 91.7% | 91.7% | 91.7% |
| MRR@3 | 0.750 | 0.750 | 0.750 | 0.750 |
| nDCG@3 | 0.779 | 0.779 | 0.779 | 0.779 |
| Citation support accuracy | 100.0% | 100.0% | 100.0% | 100.0% |
| Gold citation recall | 41.2% | 41.2% | 88.2% | 88.2% |
| Unsupported claim rate | 0.0% | 0.0% | 0.0% | 0.0% |
| Metadata slot accuracy | 51.8% | 51.8% | 100.0% | 100.0% |
| Classification accuracy | 100.0% | 100.0% | 100.0% | 100.0% |

The baseline passed 42/70 cases and the candidate passed 66/70. The candidate answered 34/38 QA cases exactly; the baseline answered 18/38. The combined change improved complete-case success by 34.3 percentage points.

## Controlled interpretation

- Replacing TF-IDF retrieval with BM25 alone did not change aggregate case success, recall@3 or MRR@3 in these runs. This is evidence of no measured improvement on this benchmark, not equivalence on all data.
- Alias-aware extraction alone produced the same case success as the combined candidate. It accounts for the observed improvement in this experiment.
- Both classifiers achieved 100% on the 16 small synthetic classification cases. This sample does not distinguish their generalization quality.
- All emitted local QA claims were literal supported field extractions, so the unsupported claim rate was 0%. The baseline still missed many correct answers: its gold citation recall was only 41.2%. Zero unsupported claims does not imply complete answers.

## Remaining failures

All four candidate failures were retrieval misses involving DRW-104 revision 02. Two status questions lacked the correct current drawing in the top three, and two comparisons retrieved the older drawing but missed the current revision. Source identity checks prevented using a different document as the answer. No test labels were used to patch these misses after observing them.

## Assignment questions

**Did changing the embedding model improve retrieval?** No neural embedding comparison was performed. The measured lexical retrieval ablation showed no change in the listed aggregate ranking metrics. The vector adapter allows a separately measured embedding experiment.

**Which LLM has the best accuracy-to-cost ratio?** This cannot be determined from the supplied local results. Local pipelines consume zero billed LLM tokens; the ratio is N/A at zero cost. Run the two configured live models with actual usage and current price snapshots.

**Did the new prompt reduce hallucinations?** No live prompt experiment was performed. The local extraction-policy change improved completeness and correctness; both local configurations already had zero unsupported emitted atomic claims. Use the two same-model prompt templates to test that question.

## Timing and historical evidence

| Configuration | Mean response (ms) | P95 response (ms) | Setup (ms) | Errors |
|---|---:|---:|---:|---:|
| baseline | 0.511 | 0.995 | 1.012 | 0 |
| retrieval_only | 0.464 | 0.886 | 0.886 | 0 |
| policy_only | 0.535 | 1.009 | 0.850 | 0 |
| candidate | 0.551 | 1.010 | 0.838 | 0 |

Timings are actual local measurements and are hardware-sensitive. They exclude index/model construction from response latency and are not LLM latency estimates. A repeated candidate run demonstrates append-only history; the table uses its latest run.

There are five recorded runs covering four distinct configurations. `docs/evidence/runs/` and `docs/evidence/history.sqlite3` retain all case-level results. `docs/evidence/comparison.html` is a standalone report. The configured quality gate passed.

The paired case bootstrap gave an exploratory complete-success difference interval of 22.9 to 45.7 percentage points for the extraction-policy/combined change. Template correlation makes this unsuitable as a production statistical-significance claim. See `methodology.md`.
