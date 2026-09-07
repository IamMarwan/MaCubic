"""OpenAI vision provider for real multimodal page analysis."""

import base64
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.settings import Settings, get_settings
from app.models.schemas import (
    BoundingBox,
    Evidence,
    ExtractedItem,
    ExtractionCategory,
    ExtractionMethod,
)
from app.services.pdf_processor import ProcessedPage
from app.services.vision_provider import VisionProvider


SYSTEM_PROMPT = """
You are a document intelligence specialist analyzing business and construction
document pages.

Extract visible information from:
- title blocks
- tables
- drawing notes
- stamps and seals
- revision information
- construction symbols
- visual annotations and markups

Return valid JSON with this exact top-level structure:
{
  "items": [
    {
      "category": "title_block | table | drawing_note | stamp | revision |
                   symbol | visual_annotation | general_text",
      "field_name": "concise snake_case name",
      "value": "string, number, list, or object",
      "confidence": 0.0,
      "evidence": {
        "quote": "visible text supporting the result, if available",
        "description": "where and how the evidence appears",
        "bounding_box": {
          "x1": 0.0,
          "y1": 0.0,
          "x2": 1.0,
          "y2": 1.0
        }
      },
      "visually_recovered": true
    }
  ]
}

Bounding-box coordinates must be normalized from 0 to 1. Set
visually_recovered to true only when the information depends on page layout,
graphics, handwriting, a stamp, a symbol, color, or other visual evidence that
ordinary embedded PDF text extraction may miss. Do not invent unreadable
values. Return an empty items list when nothing relevant is visible.
""".strip()


class VisionProviderError(RuntimeError):
    """Raised when the remote vision provider cannot return valid results."""


class OpenAIVisionProvider(VisionProvider):
    """Analyze rendered PDF pages using an OpenAI vision-capable model."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        if not self.settings.openai_api_key:
            raise VisionProviderError(
                "OPENAI_API_KEY is required when VISION_PROVIDER=openai."
            )

        self.client = AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.openai_timeout_seconds,
        )

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "openai"

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self.settings.openai_model

    async def analyze_page(
        self,
        page: ProcessedPage,
    ) -> list[ExtractedItem]:
        """Send one rendered page to the vision model."""
        encoded_image = base64.b64encode(page.image_bytes).decode("ascii")
        image_url = f"data:image/png;base64,{encoded_image}"

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Analyze document page {page.page_number}. "
                                    "Use the image as the primary source and "
                                    "the supplied PDF text only as supporting "
                                    "context.\n\nEmbedded text:\n"
                                    f"{page.text[:12000]}"
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
            )
        except Exception as exc:
            raise VisionProviderError(
                f"Vision analysis failed for page {page.page_number}: {exc}"
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise VisionProviderError(
                f"The model returned no content for page {page.page_number}."
            )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise VisionProviderError(
                f"The model returned invalid JSON for page "
                f"{page.page_number}."
            ) from exc

        raw_items = payload.get("items", [])
        if not isinstance(raw_items, list):
            raise VisionProviderError(
                "The model response field 'items' must be a list."
            )

        return [
            self._parse_item(raw_item, page.page_number)
            for raw_item in raw_items
            if isinstance(raw_item, dict)
        ]

    def _parse_item(
        self,
        raw_item: dict[str, Any],
        page_number: int,
    ) -> ExtractedItem:
        """Validate and normalize one model-generated extraction."""
        raw_category = str(raw_item.get("category", "general_text"))
        try:
            category = ExtractionCategory(raw_category)
        except ValueError:
            category = ExtractionCategory.GENERAL_TEXT

        confidence = self._clamp_confidence(
            raw_item.get("confidence", 0.5)
        )
        evidence_data = raw_item.get("evidence", {})
        if not isinstance(evidence_data, dict):
            evidence_data = {}

        return ExtractedItem(
            category=category,
            field_name=str(
                raw_item.get("field_name", "unclassified_information")
            ),
            value=raw_item.get("value", ""),
            confidence=confidence,
            page_number=page_number,
            method=ExtractionMethod.MULTIMODAL,
            evidence=Evidence(
                quote=str(evidence_data.get("quote", "")),
                description=str(evidence_data.get("description", "")),
                bounding_box=self._parse_bounding_box(
                    evidence_data.get("bounding_box")
                ),
            ),
            visually_recovered=bool(
                raw_item.get("visually_recovered", False)
            ),
        )

    @staticmethod
    def _parse_bounding_box(
        raw_box: Any,
    ) -> BoundingBox | None:
        """Parse and clamp normalized bounding-box coordinates."""
        if not isinstance(raw_box, dict):
            return None

        try:
            coordinates = {
                name: max(0.0, min(1.0, float(raw_box[name])))
                for name in ("x1", "y1", "x2", "y2")
            }
            return BoundingBox(**coordinates)
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _clamp_confidence(value: Any) -> float:
        """Convert a confidence value to the valid zero-to-one range."""
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.5