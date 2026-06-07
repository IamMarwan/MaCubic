import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


from app.classifier import classify_document
from app.extractor import extract_metadata


def test_classify_rfi():

    text = """
    Request for Information
    RFI
    Clarification required from the consultant.
    Response required before proceeding with construction works.
    """

    document_type, confidence_score = classify_document(text)

    assert document_type == "RFI"
    assert confidence_score > 0


def test_classify_drawing():

    text = """
    Structural Drawing
    Ground floor plan, section, elevation, and layout.
    """

    document_type, confidence_score = classify_document(text)

    assert document_type == "Drawing"
    assert confidence_score > 0


def test_extract_metadata():

    text = """
    Document Title: Ground Floor Structural Drawing
    Revision Number: Rev. A
    Project Name: Cubic Tower Development
    Contractor: BuildRight Contracting LLC
    Consultant: Cubic Engineering Consultancy
    Submission Date: 2026-06-07
    Discipline: Structural
    """

    metadata = extract_metadata(text)

    assert metadata["document_title"] == "Ground Floor Structural Drawing"
    assert metadata["revision_number"] == "Rev. A"
    assert metadata["project_name"] == "Cubic Tower Development"
    assert metadata["contractor"] == "BuildRight Contracting LLC"
    assert metadata["consultant"] == "Cubic Engineering Consultancy"
    assert metadata["submission_date"] == "2026-06-07"
    assert metadata["discipline"] == "Structural"