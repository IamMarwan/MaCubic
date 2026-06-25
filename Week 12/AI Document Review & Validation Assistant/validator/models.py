from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    rule_id: str
    severity: str
    message: str
    recommendation: str


class DuplicateMatch(BaseModel):
    matched_file: str
    similarity_score: float
    match_type: str


class DocumentSummary(BaseModel):
    title: str
    summary: str
    keywords: List[str]
    word_count: int
    character_count: int


class ReviewReport(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    validation_score: float
    status: str

    issues: List[ValidationIssue] = Field(default_factory=list)
    duplicate_matches: List[DuplicateMatch] = Field(default_factory=list)

    summary: Optional[DocumentSummary] = None

    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)