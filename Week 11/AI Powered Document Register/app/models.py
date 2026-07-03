from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    document_code = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    project_name = Column(String, index=True, nullable=False)
    discipline = Column(String, index=True, nullable=False)

    author = Column(String, nullable=False)
    status = Column(String, default="Draft")
    description = Column(Text)
    content = Column(Text, nullable=False)

    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)

    file_name = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    change_summary = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    document = relationship(
        "Document",
        back_populates="versions"
    )