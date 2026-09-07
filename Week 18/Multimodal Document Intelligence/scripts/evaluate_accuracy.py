"""Evaluate text-only and multimodal extraction on 20 test documents."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.core.settings import Settings
from app.models.schemas import DocumentExtractionResponse
from app.services.document_service import DocumentIntelligenceService
from app.services.mock_vision_provider import MockVisionProvider


DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"


def item_keys(
    extraction: DocumentExtractionResponse,
) -> set[tuple[str, str]]:
    """Return unique category and field-name pairs from an extraction."""
    return {
        (item.category.value, item.field_name.lower())
        for page in extraction.pages
        for item in page.items
    }


def expected_keys(
    truth: dict[str, Any],
    visual_only: bool | None = None,
) -> set[tuple[str, str]]:
    """Return expected keys, optionally filtered by visual-only status."""
    return {
        (item["category"], item["field_name"].lower())
        for item in truth["expected_items"]
        if visual_only is None or item["visual_only"] is visual_only
    }


def calculate_metrics(
    expected: set[tuple[str, str]],
    predicted: set[tuple[str, str]],
) -> dict[str, float | int]:
    """Calculate field-level precision, recall, and F1."""
    true_positives = len(expected & predicted)
    false_positives = len(predicted - expected)
    false_negatives = len(expected - predicted)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
    }


def combine_counts(
    running: dict[str, int],
    metrics: dict[str, float | int],
) -> None:
    """Add one document's confusion counts to aggregate totals."""
    for key in (
        "true_positives",
        "false_positives",
        "false_negatives",
    ):
        running[key] += int(metrics[key])


def metrics_from_counts(
    counts: dict[str, int],
) -> dict[str, float | int]:
    """Calculate final metrics from aggregate confusion counts."""
    true_positives = counts["true_positives"]
    false_positives = counts["false_positives"]
    false_negatives = counts["false_negatives"]

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        **counts,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
    }


async def evaluate() -> dict[str, Any]:
    """Evaluate all generated documents and return aggregate results."""
    settings = Settings(
        vision_provider="mock",
        save_page_images=False,
        save_extraction_results=False,
    )
    service = DocumentIntelligenceService(
        settings=settings,
        vision_provider=MockVisionProvider(),
    )

    totals = {
        "text_only": {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        },
        "multimodal": {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        },
        "visual_recovery": {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        },
    }
    document_results: list[dict[str, Any]] = []

    truth_files = sorted(GROUND_TRUTH_DIR.glob("*.json"))
    if len(truth_files) < 20:
        raise RuntimeError(
            "At least 20 ground-truth files are required. "
            "Run scripts/generate_test_documents.py first."
        )

    for truth_path in truth_files:
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        pdf_path = DOCUMENTS_DIR / truth["document"]

        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing test PDF: {pdf_path}")

        result = await service.analyze(
            pdf_bytes=pdf_path.read_bytes(),
            filename=pdf_path.name,
        )

        expected = expected_keys(truth)
        visual_expected = expected_keys(truth, visual_only=True)
        text_predicted = item_keys(result.text_only)
        multimodal_predicted = item_keys(result.multimodal)
        visual_predicted = {
            (item.category.value, item.field_name.lower())
            for page in result.multimodal.pages
            for item in page.items
            if item.visually_recovered
        }

        text_metrics = calculate_metrics(expected, text_predicted)
        multimodal_metrics = calculate_metrics(
            expected,
            multimodal_predicted,
        )
        visual_metrics = calculate_metrics(
            visual_expected,
            visual_predicted,
        )

        combine_counts(totals["text_only"], text_metrics)
        combine_counts(totals["multimodal"], multimodal_metrics)
        combine_counts(totals["visual_recovery"], visual_metrics)

        document_results.append(
            {
                "document": pdf_path.name,
                "text_only": text_metrics,
                "multimodal": multimodal_metrics,
                "visual_recovery": visual_metrics,
                "visually_recovered_count": (
                    result.comparison.visually_recovered_count
                ),
            }
        )

    return {
        "evaluation_set": {
            "document_count": len(document_results),
            "page_count": len(document_results),
            "dataset_type": "synthetic construction documents",
            "vision_provider": "mock",
        },
        "aggregate": {
            name: metrics_from_counts(counts)
            for name, counts in totals.items()
        },
        "documents": document_results,
        "limitations": [
            (
                "The evaluation dataset is synthetic and does not represent "
                "the full visual variability of real construction documents."
            ),
            (
                "The mock provider uses deterministic color-region analysis; "
                "it is not a substitute for evaluation of a real vision model."
            ),
            (
                "Field-level matching evaluates category and field name, not "
                "semantic similarity between complex values."
            ),
            (
                "Raster quality, handwriting, overlapping stamps, unusual "
                "symbols, and low-resolution scans require additional testing."
            ),
            (
                "Real-model accuracy and cost vary with model selection, "
                "prompting, page resolution, and document complexity."
            ),
        ],
    }


def percentage(value: float | int) -> str:
    """Format a zero-to-one metric as a percentage."""
    return f"{float(value) * 100:.2f}%"


def create_markdown_report(results: dict[str, Any]) -> str:
    """Create a readable accuracy and limitations report."""
    aggregate = results["aggregate"]
    dataset = results["evaluation_set"]

    return f"""# Week 18 Accuracy Report

## Evaluation Scope

- Documents evaluated: {dataset["document_count"]}
- Pages evaluated: {dataset["page_count"]}
- Dataset: {dataset["dataset_type"]}
- Automated evaluation provider: {dataset["vision_provider"]}

## Aggregate Results

| Method | Precision | Recall | F1 Score |
|---|---:|---:|---:|
| Text-only | {percentage(aggregate["text_only"]["precision"])} | {percentage(aggregate["text_only"]["recall"])} | {percentage(aggregate["text_only"]["f1_score"])} |
| Multimodal | {percentage(aggregate["multimodal"]["precision"])} | {percentage(aggregate["multimodal"]["recall"])} | {percentage(aggregate["multimodal"]["f1_score"])} |
| Visual recovery | {percentage(aggregate["visual_recovery"]["precision"])} | {percentage(aggregate["visual_recovery"]["recall"])} | {percentage(aggregate["visual_recovery"]["f1_score"])} |

## Interpretation

Text-only extraction can recover information available in the embedded PDF
text layer. Multimodal extraction adds rendered-page analysis, allowing the
service to identify visual evidence such as colored stamps and markups that
ordinary text extraction misses.

The mock provider is used for reproducible automated testing. A real
vision-capable model must be enabled for qualitative evaluation of complex
tables, drawing symbols, handwritten notes, and irregular page layouts.

## Identified Limitations

1. {results["limitations"][0]}
2. {results["limitations"][1]}
3. {results["limitations"][2]}
4. {results["limitations"][3]}
5. {results["limitations"][4]}

## Reproduction

```powershell
python scripts/generate_test_documents.py
python scripts/evaluate_accuracy.py
```

Detailed per-document metrics are saved in `accuracy_results.json`.
"""

async def main() -> None:
    """Run evaluation and save JSON and Markdown reports."""
    results = await evaluate()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = REPORTS_DIR / "accuracy_results.json"
    markdown_path = REPORTS_DIR / "accuracy_report.md"

    json_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        create_markdown_report(results),
        encoding="utf-8",
    )

    print(
        f"Evaluated "
        f"{results['evaluation_set']['document_count']} documents."
    )
    print(f"Saved detailed results to: {json_path}")
    print(f"Saved accuracy report to: {markdown_path}")


if __name__ == "__main__":
    asyncio.run(main())