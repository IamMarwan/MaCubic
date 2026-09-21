# Metrics and evaluation methodology

## Scope and provenance

This assignment measures structured construction-document QA, metadata extraction and document classification. All documents, people and projects in the benchmark are fictional. They do not represent Cubic policies or live operational decisions. The evidence reports actual program execution on this synthetic dataset.

The dataset has 105 cases: 57 QA, 24 metadata and 24 classification cases. Project Cedar Office supplies the 35 development cases; Marina Clinic and Oasis School supply 70 test cases (38 QA, 16 metadata, 16 classification). The retrieval corpus has 30 documents, including superseded revisions and similar references. Forty separate short training examples support the local classifiers. Training text differs from evaluation text; the dataset still shares templates and authoring vocabulary across splits, so these are not independently collected production holdouts.

The source corpus is the information a RAG system is supposed to retrieve, not a hidden label set. Source facts and benchmark expected values are kept in separate files and are passed only to the scorer. Providers receive an allowlisted task input and retrieved source text. This is a software interface boundary, not a security sandbox against a malicious provider implementation.

Do not tune prompts or thresholds on the test results and then present the same test split as a fresh independent validation. Use the dev split for iteration, version the benchmark, and add expert-reviewed production-derived cases before operational decisions. Expected values were authored and checked for agreement with source lines; no independent domain-expert annotation exercise was conducted for this package.

## Configuration experiments

| ID | Retrieval | Trained classifier | Extraction policy | Interpretation |
|---|---|---|---|---|
| baseline | TF-IDF cosine | TF-IDF centroid | Canonical labels only | Local baseline |
| retrieval_only | BM25 | TF-IDF centroid | Canonical labels only | Isolates retrieval |
| policy_only | TF-IDF cosine | TF-IDF centroid | Alias-aware, conflict abstention | Isolates extraction policy |
| candidate | BM25 | Multinomial Naive Bayes | Alias-aware, conflict abstention | Combined pipeline; multiple changes |

These are actual locally trained statistical classifiers, not simulated LLM outputs. TF-IDF weights use smoothed IDF and sublinear term frequency. BM25 uses k1=1.5, b=0.75 and log(1+(N-df+0.5)/(df+0.5)). Naive Bayes uses add-one smoothing. These parameters are fixed in code; no automatic tuning on the test set occurs. Classification tasks omit the title for both local and API providers.

`llm_a_baseline` / `llm_a_grounded` change only prompt content. `llm_a_grounded` / `llm_b_grounded` hold prompt and retrieval fixed while changing the configured model. Prefer pinned model snapshots where available. Repeat live experiments to assess stochastic variation; a single run does not establish stable superiority.

## Output contract

QA output consists entirely of atomic claims: source document ID, requested field, value and citations containing exact source quotations. Displayed answers are those claims; there is no additional unscored answer paragraph. Metadata values use seven canonical keys; missing values are null. Classification is one enumerated category. Values preserve dates, leading zeros and punctuation; normalization only collapses whitespace and case. QA gold facts may list accepted aliases. A refusal/abstention is an explicit boolean; it cannot coexist with claims.

## Metrics

| Metric | Definition and denominator |
|---|---|
| Retrieval recall@k | Number of relevant documents in the first k unique results divided by number of gold relevant documents. Macro average over QA cases with at least one relevant document. |
| Retrieval precision@k | Relevant hits / k, including when fewer than k documents are returned. Same eligible cases. |
| MRR@k | Reciprocal rank of first relevant hit within k; zero on a miss. Same eligible cases. |
| nDCG@k | Sum of binary relevance / log2(rank+1), divided by ideal gain for min(k, relevant count). Same eligible cases. |
| Answer correctness | Exact set equality of document/field/value claims plus correct abstention state. Extra, wrong or missing claims fail. Macro average across all QA cases, including failures. |
| Answer field F1 | 2 × correct claims / (predicted + expected claims). If both sets are empty, correct explicit abstention scores 1. |
| Abstention correctness | Whether predicted abstention agrees with the benchmark, including questions where the source exists but a field is absent. |
| Citation ID validity | Citations naming an existing corpus document / all submitted citations. Source existence alone is insufficient support. |
| Citation support accuracy | Citations that refer to the claim's source document, contain an exact source quotation, and include the annotated field line supporting the asserted value / all submitted citations. |
| Citation coverage | Predicted claims with at least one supporting citation / predicted claims. |
| Gold citation recall | Correct expected claims with a supporting citation / all expected claims. This also penalizes omitted answers and failed requests. |
| Unsupported claim rate | Unsupported or contradicted atomic QA field claims / all QA claims. This is the framework's bounded hallucination-rate measure. |
| Metadata slot accuracy | Correct values including correctly absent/null slots / all requested slots. Incorrect non-null values count as wrong. |
| Metadata non-null F1 | 2TP/(2TP+FP+FN), excluding true-null slots from TP. A wrong non-null value incurs FP and FN when a gold non-null value exists. |
| Classification accuracy | Correct class predictions / classification cases; failures count as incorrect. |
| Classification macro F1 | Unweighted per-class F1 across gold classes represented in the run, using the stored confusion matrix. |
| Complete case success | Exact QA answer, all metadata slots correct, or correct class. Averaged across the selected cases; task proportions affect this aggregate. |
| Response latency | Wall-clock milliseconds for retrieval plus provider prediction and validation; excludes model/index construction, scoring and persistence. Mean, interpolated P50/P95 are reported. Error/timeout duration is included. |
| LLM token usage | Provider-reported input, output and cached-input tokens; no character-to-token guesses. Local non-LLM execution consumes zero billed LLM tokens. Missing provider usage remains null. |
| Estimated API cost | ((input−cached) × input price + cached × cached price + output × output price) / 1,000,000. Prices are user-supplied snapshots. |
| Successful cases per USD | Number of complete successes / total known positive API cost. N/A if cost is unknown or zero. |

All denominators and micro counts are stored. Undefined metrics remain null/N/A, including a citation or hallucination rate with no submitted claims/citations. A system that refuses everything cannot earn perfect support by producing no claims; it has N/A support rates and fails answer correctness/coverage on answerable cases. A true statement about the wrong document can be supported by its own source while failing answer correctness. Support and relevance are distinct.

Retrieval cases with no relevant source are excluded from ranking metrics, because recall has no valid denominator. Their abstention and answer correctness are still evaluated. A question with a source but an absent requested field has a relevant document and remains in retrieval scoring.

Failed requests score zero on applicable task metrics and remain in the history. Invalid output schemas are failures. Malformed claims from invalid responses are not counted as valid emitted claims; the execution-error count makes that limitation visible. Extra non-task fields are schema-validated but are not included in another task's metric.

## What hallucination and citation scores cannot establish

The scorer uses a closed inventory of annotated atomic fields. It cannot judge unrestricted narrative entailment, engineering adequacy, translation quality, or arbitrary agent reasoning. A true but unannotated assertion would count as unsupported in this benchmark; extend annotations before expanding the output scope. Citation scoring deliberately demands the complete supporting field line; paraphrased or shortened quotes can fail despite appearing plausible. There is no LLM judge whose agreement is assumed to be ground truth.

## Latency, tokens and cost boundaries

Local response timings are small and hardware-sensitive. They exclude index/classifier setup, which is recorded separately as `setup_ms`. API latency includes the network call. Vector import measures cosine-scoring/retrieval only; document/query embedding generation must be timed and costed outside the runner. Vector provenance can retain external model/build notes but is not merged into per-response cost totals.

For a full corpus/index, track one-time embedding cost separately and amortize it only against an explicit expected query volume. Never compare a local non-LLM pipeline's zero API bill with a paid LLM as an infinite accuracy-to-cost advantage. Hardware, hosting, storage, taxes, provider tools, embedding calls, and unreported charges are outside the API token estimate.

When any case's token count or cost is unknown, the corresponding total is null. Known subtotals are stored separately. A missing cached-token count makes cost unknown unless cached and uncached rates are explicitly equal. The adapter does not retry automatically, avoiding untracked duplicate billed attempts. A timeout may still be billed by the provider and is reported with unknown usage if no counts were returned.

## Reproducibility and statistical interpretation

Every run records UTC timestamp, config and prompt snapshots/hashes, full dataset identity (corpus, labels and training data), selected case IDs, split, deterministic shuffle seed, code hash, metric version, Python/platform information, setup time and evidence type. Source contexts and expected/predicted outputs are retained per case. SQLite checkpoints cases and uses distinct IDs for repeated runs. Interrupted runs retain their completed cases and interrupted status.

The CLI paired comparison matches case IDs and uses 2,000 seeded paired bootstrap resamples. The displayed interval is exploratory: examples are synthetic and correlated by template/project, so an independent-case bootstrap can understate uncertainty. Do not use it as a production significance claim. For future data, use independent projects, clustered resampling and repeated live calls. The dashboard displays descriptive changes only.

## References

The design follows the principle of defining task-specific objectives, datasets and metrics before comparing configurations; typical, edge and adversarial inputs belong in evaluation. See [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices). This source is guidance, not validation of our dataset or scores.

The implementation's length-normalized lexical retrieval follows the BM25 family described in [Stanford's Introduction to Information Retrieval — Okapi BM25](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html). Exact metric conventions used here are specified in the table above and in `evalkit/metrics.py`.

The optional API adapter follows [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). Its transport/schema/error behavior was tested with injected responses, not a live account.
