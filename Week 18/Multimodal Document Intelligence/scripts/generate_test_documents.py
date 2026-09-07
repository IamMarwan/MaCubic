"""Generate 20 synthetic construction-document PDFs and ground truth."""

import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"

PAGE_WIDTH, PAGE_HEIGHT = landscape(A3)


def create_visual_overlay(
    include_stamp: bool,
    include_annotation: bool,
    include_symbol: bool,
) -> ImageReader:
    """Create visual-only evidence stored as a raster image."""
    image = Image.new("RGBA", (900, 420), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    if include_stamp:
        draw.ellipse(
            (30, 40, 330, 340),
            outline=(190, 15, 25, 255),
            width=14,
        )
        draw.ellipse(
            (55, 65, 305, 315),
            outline=(190, 15, 25, 255),
            width=5,
        )
        draw.text(
            (112, 175),
            "APPROVED",
            fill=(190, 15, 25, 255),
            font=font,
            stroke_width=1,
        )

    if include_annotation:
        annotation_points = [
            (380, 90),
            (440, 45),
            (520, 75),
            (600, 45),
            (680, 95),
            (650, 165),
            (700, 225),
            (615, 260),
            (545, 230),
            (470, 270),
            (395, 220),
            (420, 155),
        ]
        draw.line(
            annotation_points + [annotation_points[0]],
            fill=(15, 70, 210, 255),
            width=12,
            joint="curve",
        )
        draw.text(
            (490, 145),
            "CHECK AREA",
            fill=(15, 70, 210, 255),
            font=font,
        )

    if include_symbol:
        draw.line(
            [(750, 80), (850, 80), (800, 190), (750, 80)],
            fill=(20, 20, 20, 255),
            width=10,
        )
        draw.line(
            [(800, 190), (800, 325)],
            fill=(20, 20, 20, 255),
            width=10,
        )
        draw.ellipse(
            (775, 300, 825, 350),
            outline=(20, 20, 20, 255),
            width=8,
        )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def draw_title_block(
    pdf: canvas.Canvas,
    document_number: int,
    revision: str,
) -> None:
    """Draw a construction-style title block."""
    block_x = PAGE_WIDTH - 390
    block_y = 35
    block_width = 350
    block_height = 190

    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1.5)
    pdf.rect(block_x, block_y, block_width, block_height)

    for offset in (45, 85, 125, 160):
        pdf.line(
            block_x,
            block_y + offset,
            block_x + block_width,
            block_y + offset,
        )

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(block_x + 12, block_y + 168, "CUBIC ENGINEERING")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        block_x + 12,
        block_y + 140,
        f"Project Name: Multimodal Test Project {document_number:02d}",
    )
    pdf.drawString(
        block_x + 12,
        block_y + 100,
        f"Drawing Title: General Arrangement Sheet {document_number:02d}",
    )
    pdf.drawString(
        block_x + 12,
        block_y + 62,
        f"Drawing No: MDI-{document_number:03d}",
    )
    pdf.drawString(
        block_x + 185,
        block_y + 62,
        f"Revision: {revision}",
    )
    pdf.drawString(block_x + 12, block_y + 20, "Scale: 1:100")
    pdf.drawString(
        block_x + 185,
        block_y + 20,
        "Revision Date: 2026-09-07",
    )


def draw_revision_table(
    pdf: canvas.Canvas,
    document_number: int,
    revision: str,
) -> None:
    """Draw a revision table containing selectable PDF text."""
    table_data = [
        ["REV", "DATE", "DESCRIPTION", "BY"],
        [
            revision,
            "2026-09-07",
            f"Test issue {document_number:02d}",
            "ME",
        ],
    ]

    table = Table(
        table_data,
        colWidths=[50, 90, 210, 55],
        rowHeights=[24, 24],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    table.wrapOn(pdf, PAGE_WIDTH, PAGE_HEIGHT)
    table.drawOn(pdf, 65, PAGE_HEIGHT - 160)


def draw_construction_content(
    pdf: canvas.Canvas,
    document_number: int,
) -> None:
    """Draw notes, grid lines, rooms, and dimensions."""
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(65, PAGE_HEIGHT - 210, "GENERAL NOTES")

    notes = [
        "1. Verify all dimensions on site before construction.",
        "2. Do not scale this drawing.",
        "3. Coordinate structural openings with MEP services.",
    ]
    pdf.setFont("Helvetica", 10)
    for index, note in enumerate(notes):
        pdf.drawString(70, PAGE_HEIGHT - 235 - index * 20, note)

    drawing_x = 90
    drawing_y = 260
    drawing_width = 610
    drawing_height = 300

    pdf.setLineWidth(2)
    pdf.rect(drawing_x, drawing_y, drawing_width, drawing_height)
    pdf.line(
        drawing_x + 300,
        drawing_y,
        drawing_x + 300,
        drawing_y + drawing_height,
    )
    pdf.line(
        drawing_x,
        drawing_y + 145,
        drawing_x + drawing_width,
        drawing_y + 145,
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        drawing_x + 150,
        drawing_y + 220,
        f"ROOM {document_number:02d}A",
    )
    pdf.drawCentredString(
        drawing_x + 455,
        drawing_y + 220,
        f"ROOM {document_number:02d}B",
    )
    pdf.drawCentredString(
        drawing_x + 150,
        drawing_y + 70,
        "SERVICE AREA",
    )
    pdf.drawCentredString(
        drawing_x + 455,
        drawing_y + 70,
        "ACCESS ZONE",
    )

    pdf.setDash(5, 4)
    for offset in range(50, 600, 100):
        pdf.line(
            drawing_x + offset,
            drawing_y - 20,
            drawing_x + offset,
            drawing_y + drawing_height + 20,
        )
    pdf.setDash()


def ground_truth_for(
    document_number: int,
    revision: str,
    include_stamp: bool,
    include_annotation: bool,
    include_symbol: bool,
) -> dict[str, object]:
    """Build expected field metadata for one synthetic document."""
    expected_items = [
        {
            "category": "title_block",
            "field_name": "project_name",
            "value": f"Multimodal Test Project {document_number:02d}",
            "visual_only": False,
        },
        {
            "category": "title_block",
            "field_name": "drawing_title",
            "value": f"General Arrangement Sheet {document_number:02d}",
            "visual_only": False,
        },
        {
            "category": "title_block",
            "field_name": "drawing_number",
            "value": f"MDI-{document_number:03d}",
            "visual_only": False,
        },
        {
            "category": "revision",
            "field_name": "revision",
            "value": revision,
            "visual_only": False,
        },
        {
            "category": "drawing_note",
            "field_name": "note_1",
            "value": "Verify all dimensions on site before construction.",
            "visual_only": False,
        },
        {
            "category": "table",
            "field_name": "revision_table",
            "value": "Revision table",
            "visual_only": False,
        },
    ]

    if include_stamp:
        expected_items.append(
            {
                "category": "stamp",
                "field_name": "visual_stamp",
                "value": "Red approval stamp",
                "visual_only": True,
            }
        )

    if include_annotation:
        expected_items.append(
            {
                "category": "visual_annotation",
                "field_name": "colored_annotation",
                "value": "Blue review markup",
                "visual_only": True,
            }
        )

    if include_symbol:
        expected_items.append(
            {
                "category": "symbol",
                "field_name": "construction_symbol",
                "value": "Visual construction symbol",
                "visual_only": True,
            }
        )

    return {
        "document": f"construction_test_{document_number:02d}.pdf",
        "page_count": 1,
        "expected_items": expected_items,
    }


def generate_document(document_number: int) -> None:
    """Generate one PDF and its matching ground-truth JSON."""
    revision = chr(ord("A") + ((document_number - 1) % 5))
    include_stamp = document_number % 2 == 0
    include_annotation = document_number % 3 == 0
    include_symbol = document_number % 4 == 0

    pdf_path = (
        DOCUMENTS_DIR
        / f"construction_test_{document_number:02d}.pdf"
    )
    pdf = canvas.Canvas(str(pdf_path), pagesize=landscape(A3))
    pdf.setTitle(f"Construction Test Document {document_number:02d}")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(
        65,
        PAGE_HEIGHT - 60,
        f"MULTIMODAL CONSTRUCTION TEST {document_number:02d}",
    )

    draw_revision_table(pdf, document_number, revision)
    draw_construction_content(pdf, document_number)
    draw_title_block(pdf, document_number, revision)

    if include_stamp or include_annotation or include_symbol:
        overlay = create_visual_overlay(
            include_stamp=include_stamp,
            include_annotation=include_annotation,
            include_symbol=include_symbol,
        )
        pdf.drawImage(
            overlay,
            720,
            260,
            width=390,
            height=182,
            mask="auto",
            preserveAspectRatio=True,
        )

    pdf.showPage()
    pdf.save()

    truth = ground_truth_for(
        document_number=document_number,
        revision=revision,
        include_stamp=include_stamp,
        include_annotation=include_annotation,
        include_symbol=include_symbol,
    )
    truth_path = (
        GROUND_TRUTH_DIR
        / f"construction_test_{document_number:02d}.json"
    )
    truth_path.write_text(
        json.dumps(truth, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    """Generate the complete 20-document evaluation dataset."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    for document_number in range(1, 21):
        generate_document(document_number)

    print(f"Generated 20 PDF documents in: {DOCUMENTS_DIR}")
    print(f"Generated 20 ground-truth files in: {GROUND_TRUTH_DIR}")


if __name__ == "__main__":
    main()