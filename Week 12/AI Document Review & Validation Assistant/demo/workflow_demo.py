from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config import REPORT_DIR, SAMPLE_DOCUMENT_DIR, UPLOAD_DIR
from validator.reviewer import DocumentReviewer
from validator.report_generator import ReportGenerator


def create_sample_documents():
    SAMPLE_DOCUMENT_DIR.mkdir(exist_ok=True)

    valid_document = SAMPLE_DOCUMENT_DIR / "valid_project_submission.txt"
    duplicate_document = SAMPLE_DOCUMENT_DIR / "duplicate_project_submission.txt"
    missing_fields_document = SAMPLE_DOCUMENT_DIR / "missing_fields_submission.txt"

    valid_text = """
Project Document Title: Cubic Engineering Consultancy Site Review

Author: Marwan

Date: 25 June 2026

Introduction:
This document presents a site review submission for Cubic Engineering Consultancy.

Scope:
The scope includes structural review, architectural coordination, MEP coordination,
site inspection notes, and submission quality control before approval.

Project Details:
The document confirms that the reviewed package includes required project information,
client coordination notes, drawing review references, and technical observations.

Conclusion:
The document is complete and ready for submission after final internal approval.

Signature:
Approved by Cubic Engineering Consultancy.
"""

    missing_text = """
Cubic Engineering Internal Note

This short note has limited information about a possible project submission.
It does not include enough required submission details.
"""

    valid_document.write_text(valid_text.strip(), encoding="utf-8")
    duplicate_document.write_text(valid_text.strip(), encoding="utf-8")
    missing_fields_document.write_text(missing_text.strip(), encoding="utf-8")

    return [
        valid_document,
        duplicate_document,
        missing_fields_document
    ]


def copy_to_uploads(file_path: Path) -> Path:
    UPLOAD_DIR.mkdir(exist_ok=True)

    destination = UPLOAD_DIR / file_path.name
    destination.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

    return destination


def run_demo():
    print("\nAI Document Review & Validation Assistant Demo")
    print("=" * 55)

    reviewer = DocumentReviewer()
    report_generator = ReportGenerator()

    sample_files = create_sample_documents()

    for sample_file in sample_files:
        uploaded_file = copy_to_uploads(sample_file)

        print(f"\nReviewing: {uploaded_file.name}")

        report = reviewer.review_document(uploaded_file)

        json_report = report_generator.save_json_report(report, REPORT_DIR)
        pdf_report = report_generator.save_pdf_report(report, REPORT_DIR)

        print(f"Status: {report.status}")
        print(f"Validation Score: {report.validation_score}%")
        print(f"Warnings: {len(report.warnings)}")
        print(f"Recommendations: {len(report.recommendations)}")
        print(f"Duplicate Matches: {len(report.duplicate_matches)}")
        print(f"JSON Report: {json_report}")
        print(f"PDF Report: {pdf_report}")

    print("\nDemo completed successfully.")
    print("Reports saved in the reports folder.")


if __name__ == "__main__":
    run_demo()