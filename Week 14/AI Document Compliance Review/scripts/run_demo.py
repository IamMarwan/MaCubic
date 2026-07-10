import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.compliance_engine import ComplianceEngine
from app.report_generator import save_json_report, save_pdf_report


def main():
    rules_path = BASE_DIR / "config" / "rules.yaml"
    sample_dir = BASE_DIR / "data" / "samples"
    json_dir = BASE_DIR / "outputs" / "json"
    pdf_dir = BASE_DIR / "outputs" / "pdf"

    engine = ComplianceEngine(rules_path)

    documents = list(sample_dir.glob("*.docx"))

    if not documents:
        print("No sample documents found.")
        print("Run this first: python scripts/generate_samples.py")
        return

    for document_path in documents:
        report = engine.review_document(document_path)

        json_output = json_dir / f"{document_path.stem}_report.json"
        pdf_output = pdf_dir / f"{document_path.stem}_report.pdf"

        save_json_report(report, json_output)
        save_pdf_report(report, pdf_output)

        print("=" * 70)
        print(f"Document: {report.document_name}")
        print(f"Detected Type: {report.detected_document_type}")
        print(f"Compliance Score: {report.compliance_score}%")
        print(f"Passed: {report.passed_checks}")
        print(f"Failed: {report.failed_checks}")
        print(f"Warnings: {report.warning_checks}")
        print(f"JSON Report: {json_output}")
        print(f"PDF Report: {pdf_output}")


if __name__ == "__main__":
    main()