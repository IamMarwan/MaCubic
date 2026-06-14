import json

from app.database import Base, engine, SessionLocal
from app.models import Document
from app.repository import DocumentRepository
from app.schemas import DocumentCreate


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing = db.query(Document).count()

        if existing > 0:
            print("Database already seeded.")
            return

        with open(
            "dataset/sample_documents.json",
            "r",
            encoding="utf-8"
        ) as file:
            documents = json.load(file)

        repo = DocumentRepository(db)

        for item in documents:
            repo.create_document(
                DocumentCreate(**item)
            )

        print(f"Inserted {len(documents)} documents.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()