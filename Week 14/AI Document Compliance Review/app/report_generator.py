import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def save_json_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(report.to_dict(), file, indent=2)


def save_pdf_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Construction Document Compliance Report")

    y -= 35
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Document Name: {report.document_name}")

    y -= 18
    pdf.drawString(50, y, f"Detected Document Type: {report.detected_document_type}")

    y -= 18
    pdf.drawString(50, y, f"Compliance Score: {report.compliance_score}%")

    y -= 18
    pdf.drawString(
        50,
        y,
        f"Passed: {report.passed_checks} | Failed: {report.failed_checks} | Warnings: {report.warning_checks}",
    )

    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Extracted Metadata")

    pdf.setFont("Helvetica", 9)

    for key, value in report.extracted_metadata.items():
        y -= 15

        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

        pdf.drawString(60, y, f"{key}: {value}")

    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Detailed Findings")

    pdf.setFont("Helvetica", 8)

    for finding in report.findings:
        y -= 18

        if y < 70:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 8)

        line = f"[{finding.status.upper()}] {finding.title} - {finding.message}"
        pdf.drawString(60, y, line[:110])

    pdf.save()