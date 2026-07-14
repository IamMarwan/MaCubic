from pydantic import BaseModel
from typing import Optional


class DocumentBase(BaseModel):
    document_number: str
    title: str
    document_type: str
    content: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int

    class Config:
        from_attributes = True


class RelationshipBase(BaseModel):
    source_document_id: int
    target_document_id: int
    relationship_type: str
    confidence_score: int = 100
    explanation: Optional[str] = None


class RelationshipCreate(RelationshipBase):
    pass


class RelationshipResponse(RelationshipBase):
    id: int

    class Config:
        from_attributes = True


class RelatedDocument(BaseModel):
    id: int
    document_number: str
    title: str
    document_type: str
    relationship_type: str
    confidence_score: int

    class Config:
        from_attributes = True