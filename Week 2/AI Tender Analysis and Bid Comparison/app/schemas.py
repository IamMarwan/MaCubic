from typing import Literal
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    document: str
    file: str
    location_type: Literal["pdf_page", "spreadsheet_cell"]
    page: int | None = None
    sheet: str | None = None
    cell: str | None = None
    quotation: str


class Requirement(BaseModel):
    requirement_id: str
    category: str
    description: str
    status: Literal["mandatory", "optional", "unknown"] = "unknown"
    quantity: float | None = None
    unit: str | None = None
    threshold: str | None = None
    deadline: str | None = None
    value_state: dict[str, str] = Field(default_factory=dict)
    source: SourceReference
    revision: str = "1"
    supersedes: list[str] = Field(default_factory=list)
    revision_history: list[dict[str, str]] = Field(default_factory=list)
    conflict: bool = False
    conflict_note: str | None = None
    imported_at: str
    fingerprint: str


class RegisterExport(BaseModel):
    schema_version: str = "1.0"
    generated_at: str
    count: int
    requirements: list[Requirement]
