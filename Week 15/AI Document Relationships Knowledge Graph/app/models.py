from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    outgoing_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.source_document_id",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )

    incoming_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.target_document_id",
        back_populates="target_document",
        cascade="all, delete-orphan",
    )


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    target_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    confidence_score = Column(Integer, nullable=False, default=100)
    explanation = Column(Text, nullable=True)

    source_document = relationship(
        "Document",
        foreign_keys=[source_document_id],
        back_populates="outgoing_relationships",
    )

    target_document = relationship(
        "Document",
        foreign_keys=[target_document_id],
        back_populates="incoming_relationships",
    )