from pydantic import BaseModel
from typing import Optional


class Metadata(BaseModel):
    document_title: Optional[str] = None
    revision_number: Optional[str] = None
    project_name: Optional[str] = None
    contractor: Optional[str] = None
    consultant: Optional[str] = None
    submission_date: Optional[str] = None
    discipline: Optional[str] = None


class ClassificationResult(BaseModel):
    filename: str
    document_type: str
    confidence_score: float
    metadata: Metadata