from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    document_code: str
    title: str
    category: str
    project_name: str
    discipline: str
    author: str
    status: str = "Draft"
    description: Optional[str] = None
    content: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    project_name: Optional[str] = None
    discipline: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    change_summary: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    document_code: str
    title: str
    category: str
    project_name: str
    discipline: str
    author: str
    status: str
    description: Optional[str]
    content: str
    current_version: int
    created_at: datetime

    class Config:
        from_attributes = True


class VersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    file_name: str
    checksum: str
    change_summary: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    document: DocumentResponse
    score: Optional[float] = None