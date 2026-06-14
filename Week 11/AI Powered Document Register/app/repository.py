import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Document, DocumentVersion
from app.schemas import DocumentCreate, DocumentUpdate


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, data: DocumentCreate) -> Document:
        document = Document(**data.model_dump())

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            file_name=f"{document.document_code}_v1.txt",
            checksum=self._checksum(document.content),
            change_summary="Initial document version"
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_all_documents(self):
        return self.db.query(Document).all()

    def get_document_by_id(self, document_id: int):
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def get_document_by_code(self, document_code: str):
        return (
            self.db.query(Document)
            .filter(Document.document_code == document_code)
            .first()
        )

    def metadata_search(
        self,
        category: Optional[str] = None,
        project_name: Optional[str] = None,
        discipline: Optional[str] = None,
        status: Optional[str] = None,
        author: Optional[str] = None
    ):
        query = self.db.query(Document)

        if category:
            query = query.filter(Document.category.ilike(f"%{category}%"))

        if project_name:
            query = query.filter(Document.project_name.ilike(f"%{project_name}%"))

        if discipline:
            query = query.filter(Document.discipline.ilike(f"%{discipline}%"))

        if status:
            query = query.filter(Document.status.ilike(f"%{status}%"))

        if author:
            query = query.filter(Document.author.ilike(f"%{author}%"))

        return query.all()

    def update_document(
        self,
        document_id: int,
        data: DocumentUpdate
    ):
        document = self.get_document_by_id(document_id)

        if document is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        change_summary = update_data.pop("change_summary", "Document updated")

        for key, value in update_data.items():
            setattr(document, key, value)

        document.current_version += 1

        version = DocumentVersion(
            document_id=document.id,
            version_number=document.current_version,
            file_name=f"{document.document_code}_v{document.current_version}.txt",
            checksum=self._checksum(document.content),
            change_summary=change_summary
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_versions(self, document_id: int):
        return (
            self.db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
            .all()
        )

    @staticmethod
    def _checksum(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()