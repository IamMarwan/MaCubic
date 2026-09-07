"""PDF validation, text extraction, and page rendering service."""

from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from app.core.logging import get_logger
from app.core.settings import Settings, get_settings


logger = get_logger(__name__)


class PDFProcessingError(ValueError):
    """Raised when a PDF cannot be safely processed."""


@dataclass(slots=True)
class ProcessedPage:
    """Textual and visual representations of one PDF page."""

    page_number: int
    text: str
    image_bytes: bytes
    image_path: Path | None
    width: int
    height: int


class PDFProcessor:
    """Validate PDFs and convert each page into text and an image."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def process(
        self,
        pdf_bytes: bytes,
        filename: str,
        document_id: str,
    ) -> list[ProcessedPage]:
        """Extract text and render every page of a PDF."""
        self._validate_upload(pdf_bytes, filename)

        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            raise PDFProcessingError(
                "The uploaded file could not be opened as a PDF."
            ) from exc

        try:
            self._validate_document(document)
            return [
                self._process_page(document, index, document_id)
                for index in range(document.page_count)
            ]
        finally:
            document.close()

    def _validate_upload(self, pdf_bytes: bytes, filename: str) -> None:
        """Validate the uploaded filename, signature, and size."""
        if not filename.lower().endswith(".pdf"):
            raise PDFProcessingError("Only PDF files are supported.")

        if not pdf_bytes:
            raise PDFProcessingError("The uploaded PDF is empty.")

        if len(pdf_bytes) > self.settings.max_upload_size_bytes:
            raise PDFProcessingError(
                "The uploaded PDF exceeds the configured size limit of "
                f"{self.settings.max_upload_size_mb} MB."
            )

        if not pdf_bytes.lstrip().startswith(b"%PDF-"):
            raise PDFProcessingError(
                "The uploaded content does not have a valid PDF signature."
            )

    def _validate_document(self, document: fitz.Document) -> None:
        """Validate page count and encryption state."""
        if document.needs_pass:
            raise PDFProcessingError(
                "Password-protected PDFs are not supported."
            )

        if document.page_count < 1:
            raise PDFProcessingError("The PDF does not contain any pages.")

        if document.page_count > self.settings.max_pdf_pages:
            raise PDFProcessingError(
                f"The PDF contains {document.page_count} pages; the maximum "
                f"allowed is {self.settings.max_pdf_pages}."
            )

    def _process_page(
        self,
        document: fitz.Document,
        page_index: int,
        document_id: str,
    ) -> ProcessedPage:
        """Extract text and render one page as PNG."""
        page = document.load_page(page_index)
        page_number = page_index + 1
        text = page.get_text("text").strip()

        zoom = self.settings.pdf_render_dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_bytes = pixmap.tobytes("png")

        image_path: Path | None = None
        if self.settings.save_page_images:
            output_directory = self.settings.resolve_path(
                self.settings.sample_pages_dir
            ) / document_id
            output_directory.mkdir(parents=True, exist_ok=True)
            image_path = output_directory / f"page_{page_number:03d}.png"
            image_path.write_bytes(image_bytes)

        logger.info(
            "Processed page %s of %s with %s text characters",
            page_number,
            filename_or_unknown(document.name),
            len(text),
        )

        return ProcessedPage(
            page_number=page_number,
            text=text,
            image_bytes=image_bytes,
            image_path=image_path,
            width=pixmap.width,
            height=pixmap.height,
        )


def filename_or_unknown(document_name: str) -> str:
    """Return a safe display name for logging."""
    if not document_name:
        return "uploaded document"
    return Path(document_name).name