from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentRelationship

router = APIRouter(
    prefix="/relationships",
    tags=["Document Relationships"],
)


@router.get("/")
def list_relationships(db: Session = Depends(get_db)):
    relationships = db.query(DocumentRelationship).all()

    results = []

    for relationship in relationships:
        results.append(
            {
                "id": relationship.id,
                "source_document": relationship.source_document.document_number,
                "target_document": relationship.target_document.document_number,
                "relationship_type": relationship.relationship_type,
                "confidence_score": relationship.confidence_score,
                "explanation": relationship.explanation,
            }
        )

    return results


@router.get("/{document_number}")
def get_related_documents(
    document_number: str,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.document_number == document_number)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    related = []

    for relationship in document.outgoing_relationships:
        target = relationship.target_document

        related.append(
            {
                "document_number": target.document_number,
                "title": target.title,
                "document_type": target.document_type,
                "relationship_type": relationship.relationship_type,
                "confidence_score": relationship.confidence_score,
            }
        )

    return {
        "document": document.document_number,
        "related_documents": related,
    }