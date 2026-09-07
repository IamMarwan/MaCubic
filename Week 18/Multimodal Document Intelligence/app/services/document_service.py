"""Application service coordinating PDF and multimodal analysis."""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.core.settings import Settings, get_settings
from app.models.schemas import (
    ComparisonResponse,
    DocumentExtractionResponse,
    ExtractedItem,
    PageExtraction,
)
from app.services.comparison_service import ComparisonService
from app.services.pdf_processor import PDFProcessor, ProcessedPage
from app.services.provider_factory import create_vision_provider
from app.services.text_extractor import TextExtractor
from app.services.vision_provider import VisionProvider


logger = get_logger(__name__)


@dataclass(slots=True)
class AnalysisResult:
    """All outputs produced during document analysis."""

    text_only: DocumentExtractionResponse
    multimodal: DocumentExtractionResponse
    comparison: ComparisonResponse


class DocumentIntelligenceService:
    """Coordinate PDF rendering, extraction, comparison, and persistence."""

    def __init__(
        self,
        settings: Settings | None = None,
        vision_provider: VisionProvider | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.pdf_processor = PDFProcessor(self.settings)
        self.text_extractor = TextExtractor()
        self.vision_provider = (
            vision_provider or create_vision_provider(self.settings)
        )
        self.comparison_service = ComparisonService()

    async def analyze(
        self,
        pdf_bytes: bytes,
        filename: str,
    ) -> AnalysisResult:
        """Run text-only and multimodal analysis on one PDF."""
        started_at = time.perf_counter()
        document_id = self._create_document_id(pdf_bytes)

        pages = self.pdf_processor.process(
            pdf_bytes=pdf_bytes,
            filename=filename,
            document_id=document_id,
        )

        text_page_results = self._extract_text_pages(pages)
        text_elapsed = time.perf_counter() - started_at

        multimodal_started_at = time.perf_counter()
        multimodal_page_results = await self._extract_multimodal_pages(pages)
        multimodal_elapsed = time.perf_counter() - multimodal_started_at

        text_response = self._build_response(
            document_id=document_id,
            filename=filename,
            provider="pymupdf",
            model="embedded-text-and-rules",
            elapsed_seconds=text_elapsed,
            pages=text_page_results,
        )
        multimodal_response = self._build_response(
            document_id=document_id,
            filename=filename,
            provider=self.vision_provider.provider_name,
            model=self.vision_provider.model_name,
            elapsed_seconds=multimodal_elapsed,
            pages=multimodal_page_results,
        )

        comparison = self.comparison_service.compare(
            document_id=document_id,
            filename=filename,
            text_items=self._flatten_items(text_page_results),
            multimodal_items=self._flatten_items(
                multimodal_page_results
            ),
        )

        result = AnalysisResult(
            text_only=text_response,
            multimodal=multimodal_response,
            comparison=comparison,
        )

        if self.settings.save_extraction_results:
            self._save_result(result)

        logger.info(
            "Analyzed %s pages from %s in %.3f seconds",
            len(pages),
            filename,
            time.perf_counter() - started_at,
        )
        return result

    def _extract_text_pages(
        self,
        pages: list[ProcessedPage],
    ) -> list[PageExtraction]:
        """Create text-only results for all processed pages."""
        results: list[PageExtraction] = []

        for page in pages:
            items = self.text_extractor.extract(
                text=page.text,
                page_number=page.page_number,
            )
            results.append(
                PageExtraction(
                    page_number=page.page_number,
                    text_character_count=len(page.text),
                    image_path=self._display_path(page.image_path),
                    items=self._filter_confidence(items),
                    warnings=(
                        ["No embedded PDF text was detected."]
                        if not page.text
                        else []
                    ),
                )
            )

        return results

    async def _extract_multimodal_pages(
        self,
        pages: list[ProcessedPage],
    ) -> list[PageExtraction]:
        """Analyze pages concurrently with a safe concurrency limit."""
        semaphore = asyncio.Semaphore(3)

        async def analyze_one(page: ProcessedPage) -> PageExtraction:
            async with semaphore:
                items = await self.vision_provider.analyze_page(page)

            return PageExtraction(
                page_number=page.page_number,
                text_character_count=len(page.text),
                image_path=self._display_path(page.image_path),
                items=self._filter_confidence(items),
                warnings=[] if items else ["No relevant items were detected."],
            )

        return list(await asyncio.gather(*(analyze_one(page) for page in pages)))

    def _build_response(
        self,
        document_id: str,
        filename: str,
        provider: str,
        model: str,
        elapsed_seconds: float,
        pages: list[PageExtraction],
    ) -> DocumentExtractionResponse:
        """Build a complete document extraction response."""
        return DocumentExtractionResponse(
            document_id=document_id,
            filename=Path(filename).name,
            page_count=len(pages),
            provider=provider,
            model=model,
            processing_time_seconds=round(elapsed_seconds, 4),
            pages=pages,
            total_items=sum(len(page.items) for page in pages),
            warnings=[],
        )

    def _filter_confidence(
        self,
        items: list[ExtractedItem],
    ) -> list[ExtractedItem]:
        """Remove items below the configured confidence threshold."""
        return [
            item
            for item in items
            if item.confidence >= self.settings.min_confidence
        ]

    def _save_result(self, result: AnalysisResult) -> None:
        """Save extraction and comparison results as formatted JSON."""
        extraction_directory = self.settings.resolve_path(
            self.settings.extractions_dir
        )
        comparison_directory = self.settings.resolve_path(
            self.settings.comparisons_dir
        )
        extraction_directory.mkdir(parents=True, exist_ok=True)
        comparison_directory.mkdir(parents=True, exist_ok=True)

        extraction_payload = {
            "text_only": result.text_only.model_dump(mode="json"),
            "multimodal": result.multimodal.model_dump(mode="json"),
        }

        extraction_path = (
            extraction_directory
            / f"{result.multimodal.document_id}.json"
        )
        comparison_path = (
            comparison_directory
            / f"{result.comparison.document_id}.json"
        )

        extraction_path.write_text(
            json.dumps(extraction_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        comparison_path.write_text(
            result.comparison.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _flatten_items(
        pages: list[PageExtraction],
    ) -> list[ExtractedItem]:
        """Return all page items as one list."""
        return [item for page in pages for item in page.items]

    @staticmethod
    def _create_document_id(pdf_bytes: bytes) -> str:
        """Create a stable identifier from document content."""
        return hashlib.sha256(pdf_bytes).hexdigest()[:16]

    def _display_path(self, path: Path | None) -> str | None:
        """Return a project-relative path suitable for JSON output."""
        if path is None:
            return None

        try:
            return str(path.relative_to(self.settings.resolve_path(Path("."))))
        except ValueError:
            return str(path)