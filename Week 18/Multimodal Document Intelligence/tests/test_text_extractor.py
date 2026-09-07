"""Tests for text-only structured extraction."""

from app.models.schemas import ExtractionCategory, ExtractionMethod
from app.services.text_extractor import TextExtractor


def test_extract_title_block_and_revision_fields() -> None:
    """Title-block and revision values should be extracted."""
    text = """
    Project Name: Metro Station Upgrade
    Drawing Title: Ground Floor Layout
    Drawing No: ARC-101
    Revision: C
    Revision Date: 2026-09-07
    Scale: 1:100
    """
    items = TextExtractor().extract(text, page_number=2)
    values = {item.field_name: item.value for item in items}

    assert values["project_name"] == "Metro Station Upgrade"
    assert values["drawing_title"] == "Ground Floor Layout"
    assert values["drawing_number"] == "ARC-101"
    assert values["revision"] == "C"
    assert values["revision_date"] == "2026-09-07"
    assert values["scale"] == "1:100"
    assert all(item.page_number == 2 for item in items)
    assert all(
        item.method == ExtractionMethod.TEXT_ONLY for item in items
    )


def test_extract_numbered_drawing_notes() -> None:
    """Numbered drawing notes should become separate structured items."""
    text = """
    GENERAL NOTES
    1. Verify all dimensions before construction.
    2) Coordinate openings with MEP services.
    """
    items = TextExtractor().extract(text, page_number=1)
    notes = [
        item
        for item in items
        if item.category == ExtractionCategory.DRAWING_NOTE
    ]

    assert len(notes) == 2
    assert notes[0].field_name == "note_1"
    assert notes[1].field_name == "note_2"


def test_extract_pipe_separated_table() -> None:
    """Pipe-separated rows should be returned as a table."""
    text = """
    REV | DATE | DESCRIPTION | BY
    B | 2026-09-07 | Issued for construction | ME
    """
    items = TextExtractor().extract(text, page_number=1)
    tables = [
        item
        for item in items
        if item.category == ExtractionCategory.TABLE
    ]

    assert len(tables) == 1
    assert tables[0].field_name == "detected_table"
    assert len(tables[0].value["rows"]) == 2


def test_extract_approval_stamp_text() -> None:
    """Visible approval wording in the text layer should be detected."""
    items = TextExtractor().extract(
        "Status: APPROVED AS NOTED",
        page_number=1,
    )

    assert any(
        item.category == ExtractionCategory.STAMP
        and item.field_name == "approval_status"
        for item in items
    )