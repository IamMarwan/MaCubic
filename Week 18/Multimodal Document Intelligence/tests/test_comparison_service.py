"""Tests for text-only and multimodal result comparison."""

from app.models.schemas import (
    Evidence,
    ExtractedItem,
    ExtractionCategory,
    ExtractionMethod,
)
from app.services.comparison_service import ComparisonService


def create_item(
    field_name: str,
    value: str,
    method: ExtractionMethod,
    visually_recovered: bool = False,
) -> ExtractedItem:
    """Create a reusable extraction item for comparison tests."""
    return ExtractedItem(
        category=ExtractionCategory.TITLE_BLOCK,
        field_name=field_name,
        value=value,
        confidence=0.9,
        page_number=1,
        method=method,
        evidence=Evidence(description="Test evidence"),
        visually_recovered=visually_recovered,
    )


def test_comparison_identifies_agreement() -> None:
    """Equal normalized values should be marked as agreements."""
    text_item = create_item(
        "drawing_number",
        "MDI-001",
        ExtractionMethod.TEXT_ONLY,
    )
    visual_item = create_item(
        "drawing_number",
        "mdi-001",
        ExtractionMethod.MULTIMODAL,
    )

    result = ComparisonService().compare(
        document_id="doc-1",
        filename="drawing.pdf",
        text_items=[text_item],
        multimodal_items=[visual_item],
    )

    assert result.agreement_count == 1
    assert result.difference_count == 0
    assert result.items[0].status == "agreement"


def test_comparison_identifies_different_value() -> None:
    """Conflicting values should be reported as different."""
    text_item = create_item(
        "revision",
        "A",
        ExtractionMethod.TEXT_ONLY,
    )
    visual_item = create_item(
        "revision",
        "B",
        ExtractionMethod.MULTIMODAL,
    )

    result = ComparisonService().compare(
        document_id="doc-2",
        filename="drawing.pdf",
        text_items=[text_item],
        multimodal_items=[visual_item],
    )

    assert result.agreement_count == 0
    assert result.difference_count == 1
    assert result.items[0].status == "different_value"


def test_comparison_identifies_multimodal_only_item() -> None:
    """Visual-only information should be reported clearly."""
    visual_item = create_item(
        "visual_stamp",
        "Approved stamp",
        ExtractionMethod.MULTIMODAL,
        visually_recovered=True,
    )

    result = ComparisonService().compare(
        document_id="doc-3",
        filename="drawing.pdf",
        text_items=[],
        multimodal_items=[visual_item],
    )

    assert result.visually_recovered_count == 1
    assert result.difference_count == 1
    assert result.items[0].status == "multimodal_only"
    assert result.items[0].text_only_value is None