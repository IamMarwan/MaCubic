from app.database import Base, engine, SessionLocal
from app.models import Document
from app.repository import DocumentRepository
from app.schemas import DocumentCreate


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_metadata_search_by_category():
    db = SessionLocal()
    repo = DocumentRepository(db)

    repo.create_document(
        DocumentCreate(
            document_code="TEST-001",
            title="Test Structural Drawing",
            category="Drawing",
            project_name="Tower Test",
            discipline="Structural",
            author="Test Engineer",
            status="Approved",
            description="Test drawing",
            content="Structural foundation drawing test content."
        )
    )

    results = repo.metadata_search(category="Drawing")

    assert len(results) >= 1
    assert results[0].category == "Drawing"

    db.close()