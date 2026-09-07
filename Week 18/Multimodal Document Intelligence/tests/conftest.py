"""Shared pytest fixtures."""

from io import BytesIO

import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return a one-page PDF containing text and visual evidence."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 790, "Project Name: Cubic Test Project")
    pdf.drawString(50, 770, "Drawing Title: Ground Floor Plan")
    pdf.drawString(50, 750, "Drawing No: MDI-001")
    pdf.drawString(50, 730, "Revision: B")
    pdf.drawString(50, 710, "Revision Date: 2026-09-07")
    pdf.drawString(50, 680, "1. Verify all dimensions on site.")
    pdf.drawString(50, 650, "REV | DATE | DESCRIPTION | BY")
    pdf.drawString(50, 630, "B | 2026-09-07 | Test issue | ME")

    pdf.setStrokeColor(colors.red)
    pdf.setLineWidth(8)
    pdf.rect(370, 620, 145, 90)
    pdf.setFillColor(colors.red)
    pdf.drawString(405, 660, "APPROVED")

    pdf.setStrokeColor(colors.blue)
    pdf.setLineWidth(7)
    pdf.circle(430, 500, 65)
    pdf.line(365, 500, 495, 500)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()