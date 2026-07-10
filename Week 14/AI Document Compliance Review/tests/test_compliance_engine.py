import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.compliance_engine import ComplianceEngine


def test_complete_drawing_scores_high():
    engine = ComplianceEngine(BASE_DIR / "config" / "rules.yaml")

    report = engine.review_document(
        BASE_DIR / "data" / "samples" / "complete_drawing.docx"
    )

    assert report.detected_document_type == "drawing"
    assert report.compliance_score >= 90
    assert report.failed_checks == 0


def test_incomplete_method_statement_has_failures():
    engine = ComplianceEngine(BASE_DIR / "config" / "rules.yaml")

    report = engine.review_document(
        BASE_DIR / "data" / "samples" / "incomplete_method_statement.docx"
    )

    assert report.detected_document_type == "method_statement"
    assert report.failed_checks > 0
    assert report.compliance_score < 80


def test_material_submittal_missing_signature():
    engine = ComplianceEngine(BASE_DIR / "config" / "rules.yaml")

    report = engine.review_document(
        BASE_DIR / "data" / "samples" / "material_submittal_missing_signature.docx"
    )

    assert report.detected_document_type == "material_submittal"
    assert report.failed_checks > 0