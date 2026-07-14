from sqlalchemy.orm import Session

from app.models import Document


def seed_sample_documents(db: Session) -> None:
    existing_document = db.query(Document).first()

    if existing_document:
        return

    documents = [
        Document(
            document_number="RFI-001",
            title="Clarification on Lobby Ceiling Detail",
            document_type="RFI",
            content=(
                "Contractor requests clarification regarding ceiling detail "
                "shown in DWG-A-101 and specification section SPEC-09-2116."
            ),
        ),
        Document(
            document_number="DWG-A-101",
            title="Architectural Lobby Plan",
            document_type="Drawing",
            content="Lobby reflected ceiling plan and architectural details.",
        ),
        Document(
            document_number="SPEC-09-2116",
            title="Gypsum Board Assemblies",
            document_type="Specification",
            content="Technical specification for gypsum board ceiling assemblies.",
        ),
        Document(
            document_number="MM-001",
            title="Weekly Coordination Meeting Minutes",
            document_type="Meeting_Minutes",
            content=(
                "The team reviewed RFI-001 and DWG-A-101. "
                "Action item ACT-001 was assigned to the architecture team."
            ),
        ),
        Document(
            document_number="ACT-001",
            title="Resolve Lobby Ceiling Coordination",
            document_type="Action_Item",
            content="Architecture team to respond to RFI-001 and confirm DWG-A-101 details.",
        ),
    ]

    db.add_all(documents)
    db.commit()