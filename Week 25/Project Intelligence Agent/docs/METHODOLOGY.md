# Evaluation methodology

The labeled evaluation set contains ten fictional user requests and expected finding IDs. Each request is passed through the same `ProjectAgent.investigate` flow used by the demonstration. The evaluator compares the returned finding IDs with labels using aggregate counts:

- **Precision** = true positives / (true positives + false positives)
- **Recall** = true positives / (true positives + false negatives)
- **F1** = harmonic mean of precision and recall
- **Exact scenario accuracy** = scenarios whose complete finding-ID set matches the label / all scenarios
- **Citation coverage** = expected findings returned with at least one source citation / all expected findings

The labels were authored alongside the synthetic documents and have not been independently adjudicated. Results are therefore a reproducibility check for this demonstration, not an estimate of accuracy on real project records. The lexical retriever and rule-based signal selection are deterministic. No LLM, external API, token usage, or paid service is involved. Run `python run.py evaluate` to reproduce `outputs/evaluation_results.json`.
