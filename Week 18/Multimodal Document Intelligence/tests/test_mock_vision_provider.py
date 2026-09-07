"""Tests for deterministic visual page analysis."""

import pytest

from app.core.settings import Settings
from app.models.schemas import ExtractionCategory, ExtractionMethod
from app.services.mock_vision_provider import MockVisionProvider
from app.services.pdf_processor import PDFProcessor


@pytest.mark.asyncio
async def test_mock_provider_detects_visual_evidence(
    sample_pdf_bytes: bytes,
) -> None:
    """Red stamps and blue annotations should be visually recovered."""
    processor = PDFProcessor(
        Settings(
            save_page_images=False,
            pdf_render_dpi=120,
        )
    )
    page = processor.process(
        pdf_bytes=sample_pdf_bytes,
        filename="sample.pdf",
        document_id="vision-test",
    )[0]

    items = await MockVisionProvider().analyze_page(page)
    categories = {item.category for item in items}

    assert ExtractionCategory.TITLE_BLOCK in categories
    assert ExtractionCategory.STAMP in categories
    assert ExtractionCategory.VISUAL_ANNOTATION in categories
    assert all(
        item.method == ExtractionMethod.MULTIMODAL for item in items
    )

    visual_items = [item for item in items if item.visually_recovered]
    assert len(visual_items) >= 2
    assert all(
        item.evidence.bounding_box is not None
        for item in visual_items
    )


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic(
    sample_pdf_bytes: bytes,
) -> None:
    """Repeated analysis of the same page should return equal results."""
    processor = PDFProcessor(Settings(save_page_images=False))
    page = processor.process(
        pdf_bytes=sample_pdf_bytes,
        filename="sample.pdf",
        document_id="repeat-test",
    )[0]
    provider = MockVisionProvider()

    first_result = await provider.analyze_page(page)
    second_result = await provider.analyze_page(page)

    assert first_result == second_result