from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Document
from app.natural_language import NaturalLanguageQueryParser
from app.repository import DocumentRepository
from app.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from app.semantic_search import SemanticSearchEngine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Powered Document Register",
    description="Week 11 Assignment",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "AI Powered Document Register API"
    }


@app.post("/documents")
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    repo = DocumentRepository(db)

    created = repo.create_document(document)

    return created


@app.get(
    "/documents",
    response_model=list[DocumentResponse]
)
def get_documents(
    db: Session = Depends(get_db)
):
    repo = DocumentRepository(db)

    return repo.get_all_documents()


@app.get(
    "/documents/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    repo = DocumentRepository(db)

    document = repo.get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@app.put("/documents/{document_id}")
def update_document(
    document_id: int,
    update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    repo = DocumentRepository(db)

    document = repo.update_document(
        document_id,
        update
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@app.get("/search/metadata")
def metadata_search(
    category: str | None = None,
    project_name: str | None = None,
    discipline: str | None = None,
    status: str | None = None,
    author: str | None = None,
    db: Session = Depends(get_db)
):
    repo = DocumentRepository(db)

    return repo.metadata_search(
        category=category,
        project_name=project_name,
        discipline=discipline,
        status=status,
        author=author
    )


@app.get("/search/semantic")
def semantic_search(
    query: str,
    db: Session = Depends(get_db)
):
    documents = db.query(Document).all()

    engine = SemanticSearchEngine()

    results = engine.search(
        query=query,
        documents=documents
    )

    return [
        {
            "document_id": doc.id,
            "title": doc.title,
            "score": round(float(score), 4)
        }
        for doc, score in results
    ]


@app.get("/search/natural")
def natural_language_search(
    query: str,
    db: Session = Depends(get_db)
):
    parser = NaturalLanguageQueryParser()

    filters = parser.parse(query)

    repo = DocumentRepository(db)

    return repo.metadata_search(
        category=filters["category"],
        project_name=filters["project_name"],
        discipline=filters["discipline"],
        status=filters["status"],
        author=filters["author"]
    )