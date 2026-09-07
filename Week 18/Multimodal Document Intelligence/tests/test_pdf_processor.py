"""Tests for PDF validation, text extraction, and rendering."""

import pytest

from app.core.settings import Settings
from app.services.pdf_processor import PDFProcessingError, PDFProcessor


def test_process_valid_pdf(
    sample_pdf_bytes: bytes,
    tmp_path,
) -> None:
    """A valid PDF should produce text and a rendered page image."""
    settings = Settings(
        sample_pages_dir=tmp_path / "pages",
        save_page_images=True,
        max_pdf_pages=10,
    )
    processor = PDFProcessor(settings)

    pages = processor.process(
        pdf_bytes=sample_pdf_bytes,
        filename="sample.pdf",
        document_id="test-document",
    )

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Cubic Test Project" in pages[0].text
    assert pages[0].image_bytes.startswith(b"\x89PNG")
    assert pages[0].image_path is not None
    assert pages[0].image_path.exists()
    assert pages[0].width > 0
    assert pages[0].height > 0


def test_reject_non_pdf_extension() -> None:
    """Uploads without a PDF extension should be rejected."""
    processor = PDFProcessor(Settings())

    with pytest.raises(PDFProcessingError, match="Only PDF"):
        processor.process(
            pdf_bytes=b"%PDF-1.4",
            filename="document.txt",
            document_id="invalid",
        )


def test_reject_invalid_pdf_signature() -> None:
    """Content without a PDF signature should be rejected."""
    processor = PDFProcessor(Settings())

    with pytest.raises(PDFProcessingError, match="signature"):
        processor.process(
            pdf_bytes=b"This is not a PDF.",
            filename="document.pdf",
            document_id="invalid",
        )


def test_reject_empty_pdf() -> None:
    """An empty upload should be rejected."""
    processor = PDFProcessor(Settings())

    with pytest.raises(PDFProcessingError, match="empty"):
        processor.process(
            pdf_bytes=b"",
            filename="document.pdf",
            document_id="invalid",
        )