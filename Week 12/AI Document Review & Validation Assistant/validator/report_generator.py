import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors

from validator.models import ReviewReport


class ReportGenerator:
    def save_json_report(self, report: ReviewReport, output_dir: Path) -> Path:
        output_dir.mkdir(exist_ok=True)

        report_path = output_dir / f"{Path(report.file_name).stem}_review_report.json"

        with open(report_path, "w", encoding="utf-8") as file:
            json.dump(report.model_dump(), file, indent=4)

        return report_path

    def save_pdf_report(self, report: ReviewReport, output_dir: Path) -> Path:
        output_dir.mkdir(exist_ok=True)

        report_path = output_dir / f"{Path(report.file_name).stem}_review_report.pdf"

        document = SimpleDocTemplate(
            str(report_path),
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AI Document Review Report", styles["Title"]))
        story.append(Spacer(1, 12))

        summary_table = Table([
            ["File Name", report.file_name],
            ["File Type", report.file_type],
            ["File Size", f"{report.file_size} bytes"],
            ["Status", report.status],
            ["Validation Score", f"{report.validation_score}%"],
        ])

        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 16))

        story.append(Paragraph("Document Summary", styles["Heading2"]))

        if report.summary:
            story.append(Paragraph(report.summary.summary, styles["BodyText"]))
            story.append(Spacer(1, 8))
            story.append(
                Paragraph(
                    f"Keywords: {', '.join(report.summary.keywords)}",
                    styles["BodyText"]
                )
            )
        else:
            story.append(Paragraph("No summary available.", styles["BodyText"]))

        story.append(Spacer(1, 16))

        story.append(Paragraph("Validation Issues", styles["Heading2"]))

        if report.issues:
            issue_data = [["Severity", "Message", "Recommendation"]]

            for issue in report.issues:
                issue_data.append([
                    issue.severity,
                    issue.message,
                    issue.recommendation
                ])

            issue_table = Table(issue_data, colWidths=[70, 190, 220])
            issue_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))

            story.append(issue_table)
        else:
            story.append(Paragraph("No validation issues detected.", styles["BodyText"]))

        story.append(Spacer(1, 16))

        story.append(Paragraph("Duplicate Detection", styles["Heading2"]))

        if report.duplicate_matches:
            duplicate_data = [["Matched File", "Score", "Match Type"]]

            for duplicate in report.duplicate_matches:
                duplicate_data.append([
                    duplicate.matched_file,
                    f"{duplicate.similarity_score}%",
                    duplicate.match_type
                ])

            duplicate_table = Table(duplicate_data, colWidths=[200, 80, 200])
            duplicate_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))

            story.append(duplicate_table)
        else:
            story.append(Paragraph("No duplicate matches detected.", styles["BodyText"]))

        story.append(Spacer(1, 16))

        story.append(Paragraph("Warnings", styles["Heading2"]))

        for warning in report.warnings:
            story.append(Paragraph(f"- {warning}", styles["BodyText"]))

        story.append(Spacer(1, 16))

        story.append(Paragraph("Recommendations", styles["Heading2"]))

        for recommendation in report.recommendations:
            story.append(Paragraph(f"- {recommendation}", styles["BodyText"]))

        document.build(story)

        return report_path