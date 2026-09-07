# Week 18 Accuracy Report

## Evaluation Scope

- Documents evaluated: 20
- Pages evaluated: 20
- Dataset: synthetic construction documents
- Automated evaluation provider: mock

## Aggregate Results

| Method | Precision | Recall | F1 Score |
|---|---:|---:|---:|
| Text-only | 55.56% | 70.92% | 62.31% |
| Multimodal | 59.18% | 82.27% | 68.84% |
| Visual recovery | 100.00% | 76.19% | 86.49% |

## Interpretation

Text-only extraction can recover information available in the embedded PDF
text layer. Multimodal extraction adds rendered-page analysis, allowing the
service to identify visual evidence such as colored stamps and markups that
ordinary text extraction misses.

The mock provider is used for reproducible automated testing. A real
vision-capable model must be enabled for qualitative evaluation of complex
tables, drawing symbols, handwritten notes, and irregular page layouts.

## Identified Limitations

1. The evaluation dataset is synthetic and does not represent the full visual variability of real construction documents.
2. The mock provider uses deterministic color-region analysis; it is not a substitute for evaluation of a real vision model.
3. Field-level matching evaluates category and field name, not semantic similarity between complex values.
4. Raster quality, handwriting, overlapping stamps, unusual symbols, and low-resolution scans require additional testing.
5. Real-model accuracy and cost vary with model selection, prompting, page resolution, and document complexity.

## Reproduction

```powershell
python scripts/generate_test_documents.py
python scripts/evaluate_accuracy.py
```

Detailed per-document metrics are saved in `accuracy_results.json`.
