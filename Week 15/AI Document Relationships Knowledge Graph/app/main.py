from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.relationships import router as relationship_router
from app.database import Base, SessionLocal, engine
from app.models import Document, DocumentRelationship
from app.relationship_engine import RelationshipEngine
from app.sample_data import seed_sample_documents

app = FastAPI(
    title="AI Document Relationships & Knowledge Graph",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(relationship_router)


@app.on_event("startup")
def startup():
    db: Session = SessionLocal()

    try:
        # Load sample documents once
        seed_sample_documents(db)

        # Don't rebuild relationships if they already exist
        if db.query(DocumentRelationship).count() == 0:

            documents = db.query(Document).all()

            engine_instance = RelationshipEngine()
            relationships = engine_instance.build_relationships(documents)

            db.add_all(relationships)
            db.commit()

    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "AI Document Relationships & Knowledge Graph API",
        "documentation": "/docs",
        "graph_viewer": "/graph",
        "relationships": "/relationships",
    }


@app.get("/graph")
def graph_viewer():
    return FileResponse("static/graph_viewer.html")