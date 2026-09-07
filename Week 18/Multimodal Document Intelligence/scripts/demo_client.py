"""Call the running API and save a complete demonstration result."""

import argparse
import json
from pathlib import Path

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENT = (
    PROJECT_ROOT
    / "data"
    / "sample_documents"
    / "construction_test_12.pdf"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "extractions" / "demo_result.json"


def parse_arguments() -> argparse.Namespace:
    """Parse optional command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the multimodal document intelligence demonstration."
    )
    parser.add_argument(
        "--document",
        type=Path,
        default=DEFAULT_DOCUMENT,
        help="PDF document to analyze.",
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000/api/v1/analyze",
        help="URL of the running analysis endpoint.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSON file used to save the API response.",
    )
    return parser.parse_args()


def main() -> None:
    """Upload a sample PDF and display the comparison summary."""
    arguments = parse_arguments()
    document_path = arguments.document.resolve()

    if not document_path.exists():
        raise SystemExit(
            f"Document not found: {document_path}\n"
            "Run scripts/generate_test_documents.py first."
        )

    with document_path.open("rb") as pdf_file:
        response = httpx.post(
            arguments.api_url,
            files={
                "file": (
                    document_path.name,
                    pdf_file,
                    "application/pdf",
                )
            },
            timeout=180,
        )

    response.raise_for_status()
    result = response.json()

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    text_result = result["text_only"]
    multimodal_result = result["multimodal"]
    comparison = result["comparison"]

    print("\nMultimodal Document Intelligence Demonstration")
    print("=" * 50)
    print(f"Document: {document_path.name}")
    print(f"Pages: {multimodal_result['page_count']}")
    print(f"Vision provider: {multimodal_result['provider']}")
    print(f"Vision model: {multimodal_result['model']}")
    print(f"Text-only items: {text_result['total_items']}")
    print(f"Multimodal items: {multimodal_result['total_items']}")
    print(
        "Visually recovered items: "
        f"{comparison['visually_recovered_count']}"
    )
    print(f"Agreements: {comparison['agreement_count']}")
    print(f"Differences: {comparison['difference_count']}")
    print(f"Saved complete JSON result to: {arguments.output}")


if __name__ == "__main__":
    main()