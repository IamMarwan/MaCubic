"""Pydantic models used by the extraction and comparison APIs."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExtractionCategory(StrEnum):
    """Supported document information categories."""

    TITLE_BLOCK = "title_block"
    TABLE = "table"
    DRAWING_NOTE = "drawing_note"
    STAMP = "stamp"
    REVISION = "revision"
    SYMBOL = "symbol"
    VISUAL_ANNOTATION = "visual_annotation"
    GENERAL_TEXT = "general_text"


class ExtractionMethod(StrEnum):
    """Method responsible for extracting an item."""

    TEXT_ONLY = "text_only"
    MULTIMODAL = "multimodal"


class BoundingBox(BaseModel):
    """Normalized evidence location on a page."""

    x1: float = Field(ge=0.0, le=1.0)
    y1: float = Field(ge=0.0, le=1.0)
    x2: float = Field(ge=0.0, le=1.0)
    y2: float = Field(ge=0.0, le=1.0)


class Evidence(BaseModel):
    """Evidence supporting an extracted item."""

    quote: str = ""
    description: str = ""
    bounding_box: BoundingBox | None = None


class ExtractedItem(BaseModel):
    """One structured item extracted from a document page."""

    category: ExtractionCategory
    field_name: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    page_number: int = Field(ge=1)
    method: ExtractionMethod
    evidence: Evidence
    visually_recovered: bool = False


class PageExtraction(BaseModel):
    """Extraction result for one PDF page."""

    page_number: int = Field(ge=1)
    text_character_count: int = Field(ge=0)
    image_path: str | None = None
    items: list[ExtractedItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentExtractionResponse(BaseModel):
    """Complete structured extraction result for one document."""

    document_id: str
    filename: str
    page_count: int = Field(ge=1)
    provider: str
    model: str
    processing_time_seconds: float = Field(ge=0.0)
    pages: list[PageExtraction]
    total_items: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class ComparisonItem(BaseModel):
    """Comparison of a field across extraction methods."""

    page_number: int = Field(ge=1)
    category: ExtractionCategory
    field_name: str
    text_only_value: Any | None = None
    multimodal_value: Any | None = None
    text_only_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    multimodal_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    status: str
    explanation: str


class ComparisonResponse(BaseModel):
    """Text-only versus multimodal comparison result."""

    document_id: str
    filename: str
    text_only_item_count: int = Field(ge=0)
    multimodal_item_count: int = Field(ge=0)
    visually_recovered_count: int = Field(ge=0)
    agreement_count: int = Field(ge=0)
    difference_count: int = Field(ge=0)
    items: list[ComparisonItem] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Service health information."""

    status: str
    application: str
    version: str
    vision_provider: str
    model: str