"""Deterministic local vision provider used for tests and demonstrations."""

from io import BytesIO

from PIL import Image, ImageStat

from app.models.schemas import (
    BoundingBox,
    Evidence,
    ExtractedItem,
    ExtractionCategory,
    ExtractionMethod,
)
from app.services.pdf_processor import ProcessedPage
from app.services.text_extractor import TextExtractor
from app.services.vision_provider import VisionProvider


class MockVisionProvider(VisionProvider):
    """
    Simulate multimodal extraction without calling an external API.

    The provider promotes text-layer results to multimodal results and uses
    basic pixel analysis to detect colored stamps and annotations. It is
    deterministic and is intended for automated testing, not production AI.
    """

    def __init__(self) -> None:
        self.text_extractor = TextExtractor()

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "mock"

    @property
    def model_name(self) -> str:
        """Return the local model identifier."""
        return "deterministic-visual-analyzer-v1"

    async def analyze_page(
        self,
        page: ProcessedPage,
    ) -> list[ExtractedItem]:
        """Analyze page text and rendered pixels."""
        items = self._promote_text_items(page)
        items.extend(self._detect_colored_regions(page))
        return self._remove_duplicates(items)

    def _promote_text_items(
        self,
        page: ProcessedPage,
    ) -> list[ExtractedItem]:
        """Convert text-only results into multimodal results."""
        promoted_items: list[ExtractedItem] = []

        for item in self.text_extractor.extract(
            page.text,
            page.page_number,
        ):
            promoted_items.append(
                item.model_copy(
                    update={
                        "method": ExtractionMethod.MULTIMODAL,
                        "confidence": min(item.confidence + 0.08, 0.99),
                        "evidence": Evidence(
                            quote=item.evidence.quote,
                            description=(
                                "Confirmed using the rendered page and the "
                                "embedded PDF text layer."
                            ),
                        ),
                    }
                )
            )

        return promoted_items

    def _detect_colored_regions(
        self,
        page: ProcessedPage,
    ) -> list[ExtractedItem]:
        """Detect likely red stamps and blue visual annotations."""
        image = Image.open(BytesIO(page.image_bytes)).convert("RGB")
        thumbnail = image.copy()
        thumbnail.thumbnail((700, 700))

        red_box, red_ratio = self._color_region(
            thumbnail,
            color="red",
        )
        blue_box, blue_ratio = self._color_region(
            thumbnail,
            color="blue",
        )

        items: list[ExtractedItem] = []

        if red_box is not None and red_ratio >= 0.0005:
            items.append(
                ExtractedItem(
                    category=ExtractionCategory.STAMP,
                    field_name="visual_stamp",
                    value="Red stamp or seal detected",
                    confidence=min(0.70 + red_ratio * 20, 0.95),
                    page_number=page.page_number,
                    method=ExtractionMethod.MULTIMODAL,
                    evidence=Evidence(
                        description=(
                            "A concentrated red-colored region was detected "
                            "on the rendered page."
                        ),
                        bounding_box=red_box,
                    ),
                    visually_recovered=True,
                )
            )

        if blue_box is not None and blue_ratio >= 0.0005:
            items.append(
                ExtractedItem(
                    category=ExtractionCategory.VISUAL_ANNOTATION,
                    field_name="colored_annotation",
                    value="Blue markup or annotation detected",
                    confidence=min(0.68 + blue_ratio * 20, 0.93),
                    page_number=page.page_number,
                    method=ExtractionMethod.MULTIMODAL,
                    evidence=Evidence(
                        description=(
                            "A concentrated blue-colored region was detected "
                            "on the rendered page."
                        ),
                        bounding_box=blue_box,
                    ),
                    visually_recovered=True,
                )
            )

        return items

    @staticmethod
    def _color_region(
        image: Image.Image,
        color: str,
    ) -> tuple[BoundingBox | None, float]:
        """Return a normalized bounding box and ratio for a target color."""
        width, height = image.size
        matching_points: list[tuple[int, int]] = []

        pixels = image.load()
        if pixels is None:
            return None, 0.0

        for y in range(height):
            for x in range(width):
                red, green, blue = pixels[x, y]

                is_match = (
                    red > 140 and red > green * 1.35 and red > blue * 1.35
                    if color == "red"
                    else blue > 130
                    and blue > red * 1.25
                    and blue > green * 1.10
                )

                if is_match:
                    matching_points.append((x, y))

        if not matching_points:
            return None, 0.0

        x_values = [point[0] for point in matching_points]
        y_values = [point[1] for point in matching_points]
        ratio = len(matching_points) / (width * height)

        box = BoundingBox(
            x1=min(x_values) / width,
            y1=min(y_values) / height,
            x2=(max(x_values) + 1) / width,
            y2=(max(y_values) + 1) / height,
        )
        return box, ratio

    @staticmethod
    def _remove_duplicates(
        items: list[ExtractedItem],
    ) -> list[ExtractedItem]:
        """Remove duplicate multimodal extraction items."""
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