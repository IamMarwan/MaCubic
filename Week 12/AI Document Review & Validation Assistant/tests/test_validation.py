from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from validator.validation_engine import ValidationEngine


def test_valid_document_has_no_critical_issues(tmp_path):
    file_path = tmp_path / "valid_document.txt"

    file_path.write_text(
        """
        Title: Site Inspection Report
        Author: Marwan
        Date: 25 June 2026

        Introduction:
        This document explains the purpose of the inspection report.

        Scope:
        The scope includes review of site progress, safety notes,
        technical comments, and required approval steps.

        Conclusion:
        The document is ready for review.

        Signature:
        Approved by Cubic Engineering Consultancy.
        """,
        encoding="utf-8"
    )

    engine = ValidationEngine()
    issues = engine.run_validation(file_path)

    assert not any(issue.severity == "critical" for issue in issues)


def test_empty_document_fails_validation(tmp_path):
    file_path = tmp_path / "empty_document.txt"
    file_path.write_text("", encoding="utf-8")

    engine = ValidationEngine()
    issues = engine.run_validation(file_path)

    assert any(issue.rule_id == "CONTENT_001" for issue in issues)


def test_missing_required_fields_are_detected(tmp_path):
    file_path = tmp_path / "missing_fields.txt"

    file_path.write_text(
        "This is a basic document without clear metadata.",
        encoding="utf-8"
    )

    engine = ValidationEngine()
    issues = engine.run_validation(file_path)

    issue_messages = [issue.message.lower() for issue in issues]

    assert any("missing required field" in message for message in issue_messages)