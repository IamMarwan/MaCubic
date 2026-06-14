from app.database import SessionLocal
from app.models import Document
from app.natural_language import NaturalLanguageQueryParser
from app.repository import DocumentRepository
from app.semantic_search import SemanticSearchEngine


def run_demo():
    db = SessionLocal()

    try:
        repo = DocumentRepository(db)

        print("\n--- Traditional Metadata Search ---")
        metadata_results = repo.metadata_search(
            category="Drawing",
            discipline="Structural"
        )

        for document in metadata_results:
            print(
                f"{document.document_code} | "
                f"{document.title} | "
                f"{document.category} | "
                f"{document.discipline}"
            )

        print("\n--- Semantic AI Search ---")
        documents = db.query(Document).all()
        semantic_engine = SemanticSearchEngine()

        semantic_results = semantic_engine.search(
            query="concrete foundation structure",
            documents=documents
        )

        for document, score in semantic_results:
            print(
                f"{document.document_code} | "
                f"{document.title} | "
                f"Score: {score:.4f}"
            )

        print("\n--- Natural Language Query ---")
        parser = NaturalLanguageQueryParser()
        filters = parser.parse(
            "show me approved structural drawings for tower a"
        )

        nl_results = repo.metadata_search(**filters)

        for document in nl_results:
            print(
                f"{document.document_code} | "
                f"{document.title} | "
                f"{document.status}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()