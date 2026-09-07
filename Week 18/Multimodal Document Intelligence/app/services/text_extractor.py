"""Rule-based text-only extraction for comparison with vision results."""

import re
from dataclasses import dataclass

from app.models.schemas import (
    Evidence,
    ExtractedItem,
    ExtractionCategory,
    ExtractionMethod,
)


@dataclass(frozen=True, slots=True)
class FieldPattern:
    """A labeled regular-expression extraction rule."""

    category: ExtractionCategory
    field_name: str
    pattern: re.Pattern[str]


FIELD_PATTERNS = (
    FieldPattern(
        ExtractionCategory.TITLE_BLOCK,
        "project_name",
        re.compile(
            r"(?:project|project name)\s*[:\-]\s*(.+)",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.TITLE_BLOCK,
        "drawing_title",
        re.compile(
            r"(?:drawing title|title)\s*[:\-]\s*(.+)",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.TITLE_BLOCK,
        "drawing_number",
        re.compile(
            r"(?:drawing no\.?|drawing number|dwg\.?\s*no\.?)"
            r"\s*[:\-]\s*([A-Z0-9._\-/]+)",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.TITLE_BLOCK,
        "scale",
        re.compile(
            r"(?:scale)\s*[:\-]\s*([A-Z0-9.:/\-\s]+)",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.REVISION,
        "revision",
        re.compile(
            r"(?:revision|rev\.?)\s*[:\-]\s*([A-Z0-9._\-/]+)",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.REVISION,
        "revision_date",
        re.compile(
            r"(?:revision date|rev\.?\s*date|date)"
            r"\s*[:\-]\s*([0-9]{1,4}[/.\-][0-9]{1,2}[/.\-][0-9]{1,4})",
            re.IGNORECASE,
        ),
    ),
    FieldPattern(
        ExtractionCategory.STAMP,
        "approval_status",
        re.compile(
            r"\b(approved|approved as noted|reviewed|rejected|"
            r"for construction|not for construction)\b",
            re.IGNORECASE,
        ),
    ),
)


class TextExtractor:
    """Extract structured fields using only the PDF text layer."""

    def extract(self, text: str, page_number: int) -> list[ExtractedItem]:
        """Return structured items detected in one page's text."""
        normalized_text = self._normalize(text)
        items: list[ExtractedItem] = []

        for field_pattern in FIELD_PATTERNS:
            match = field_pattern.pattern.search(normalized_text)
            if match:
                value = self._clean_value(match.group(1))
                if value:
                    items.append(
                        self._create_item(
                            category=field_pattern.category,
                            field_name=field_pattern.field_name,
                            value=value,
                            page_number=page_number,
                            quote=match.group(0),
                            confidence=0.82,
                        )
                    )

        items.extend(self._extract_notes(normalized_text, page_number))
        items.extend(self._extract_table_rows(normalized_text, page_number))
        return self._remove_duplicates(items)

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize whitespace while preserving line boundaries."""
        lines = [
            re.sub(r"[ \t]+", " ", line).strip()
            for line in text.replace("\r", "\n").splitlines()
        ]
        return "\n".join(line for line in lines if line)

    @staticmethod
    def _clean_value(value: str) -> str:
        """Clean a captured field value."""
        return re.sub(r"\s+", " ", value).strip(" :-\t")

    def _extract_notes(
        self,
        text: str,
        page_number: int,
    ) -> list[ExtractedItem]:
        """Extract numbered notes from the text layer."""
        items: list[ExtractedItem] = []
        note_pattern = re.compile(
            r"^(?:note\s*)?(\d{1,2})[.)]\s+(.{4,250})$",
            re.IGNORECASE | re.MULTILINE,
        )

        for number, note in note_pattern.findall(text):
            value = self._clean_value(note)
            items.append(
                self._create_item(
                    category=ExtractionCategory.DRAWING_NOTE,
                    field_name=f"note_{number}",
                    value=value,
                    page_number=page_number,
                    quote=f"{number}. {value}",
                    confidence=0.76,
                )
            )

        return items

    def _extract_table_rows(
        self,
        text: str,
        page_number: int,
    ) -> list[ExtractedItem]:
        """Identify likely pipe-separated table rows."""
        rows = []
        for line in text.splitlines():
            if line.count("|") >= 2:
                cells = [
                    self._clean_value(cell)
                    for cell in line.split("|")
                    if self._clean_value(cell)
                ]
                if len(cells) >= 3:
                    rows.append(cells)

        if not rows:
            return []

        return [
            self._create_item(
                category=ExtractionCategory.TABLE,
                field_name="detected_table",
                value={"rows": rows},
                page_number=page_number,
                quote="\n".join(" | ".join(row) for row in rows),
                confidence=0.68,
            )
        ]

    @staticmethod
    def _create_item(
        category: ExtractionCategory,
        field_name: str,
        value: object,
        page_number: int,
        quote: str,
        confidence: float,
    ) -> ExtractedItem:
        """Create a text-only extraction item."""
        return ExtractedItem(
            category=category,
            field_name=field_name,
            value=value,
            confidence=confidence,
            page_number=page_number,
            method=ExtractionMethod.TEXT_ONLY,
            evidence=Evidence(
                quote=quote,
                description="Matched in the embedded PDF text layer.",
            ),
            visually_recovered=False,
        )

    @staticmethod
    def _remove_duplicates(
        items: list[ExtractedItem],
    ) -> list[ExtractedItem]:
        """Remove repeated category, field, and value combinations."""
        unique_items: list[ExtractedItem] = []
        seen: set[tuple[str, str, str]] = set()

        for item in items:
            key = (
                item.category.value,
                item.field_name.lower(),
                str(item.value).strip().lower(),
            )
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items