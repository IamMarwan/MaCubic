from app.models import Document
from app.relationship_engine import RelationshipEngine


def test_rfi_references_drawing():
    rfi = Document(
        id=1,
        document_number="RFI-001",
        title="Ceiling Clarification",
        document_type="RFI",
        content="Please clarify ceiling detail shown in DWG-A-101.",
    )

    drawing = Document(
        id=2,
        document_number="DWG-A-101",
        title="Lobby Ceiling Plan",
        document_type="Drawing",
        content="Architectural lobby ceiling plan.",
    )

    engine = RelationshipEngine()
    relationships = engine.build_relationships([rfi, drawing])

    assert len(relationships) == 1
    assert relationships[0].relationship_type == "RFI_REFERENCES_DRAWING"
    assert relationships[0].source_document_id == 1
    assert relationships[0].target_document_id == 2


def test_meeting_minutes_reference_action_item():
    meeting_minutes = Document(
        id=1,
        document_number="MM-001",
        title="Weekly Coordination Meeting",
        document_type="Meeting_Minutes",
        content="Action item ACT-001 was assigned to the architecture team.",
    )

    action_item = Document(
        id=2,
        document_number="ACT-001",
        title="Resolve Ceiling Detail",
        document_type="Action_Item",
        content="Respond to RFI-001.",
    )

    engine = RelationshipEngine()
    relationships = engine.build_relationships([meeting_minutes, action_item])

    assert len(relationships) == 1
    assert relationships[0].relationship_type == "MEETING_MINUTES_ASSIGN_ACTION_ITEM"


def test_no_relationship_when_no_reference_exists():
    rfi = Document(
        id=1,
        document_number="RFI-001",
        title="Door Hardware Clarification",
        document_type="RFI",
        content="Please clarify door hardware schedule.",
    )

    drawing = Document(
        id=2,
        document_number="DWG-A-101",
        title="Lobby Ceiling Plan",
        document_type="Drawing",
        content="Architectural lobby ceiling plan.",
    )

    engine = RelationshipEngine()
    relationships = engine.build_relationships([rfi, drawing])

    assert relationships == []