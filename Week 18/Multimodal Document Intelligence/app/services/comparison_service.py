"""Compare text-only and multimodal document extraction results."""

import json
from collections import defaultdict

from app.models.schemas import (
    ComparisonItem,
    ComparisonResponse,
    ExtractedItem,
)


class ComparisonService:
    """Identify agreements, differences, and visually recovered fields."""

    def compare(
        self,
        document_id: str,
        filename: str,
        text_items: list[ExtractedItem],
        multimodal_items: list[ExtractedItem],
    ) -> ComparisonResponse:
        """Compare extraction items using page, category, and field name."""
        text_groups = self._group_items(text_items)
        multimodal_groups = self._group_items(multimodal_items)

        all_keys = sorted(set(text_groups) | set(multimodal_groups))
        comparisons: list[ComparisonItem] = []

        for key in all_keys:
            text_group = text_groups.get(key, [])
            multimodal_group = multimodal_groups.get(key, [])
            pair_count = max(len(text_group), len(multimodal_group))

            for index in range(pair_count):
                text_item = (
                    text_group[index]
                    if index < len(text_group)
                    else None
                )
                multimodal_item = (
                    multimodal_group[index]
                    if index < len(multimodal_group)
                    else None
                )
                comparisons.append(
                    self._compare_pair(
                        key,
                        text_item,
                        multimodal_item,
                    )
                )

        agreement_count = sum(
            item.status == "agreement" for item in comparisons
        )
        difference_count = len(comparisons) - agreement_count

        return ComparisonResponse(
            document_id=document_id,
            filename=filename,
            text_only_item_count=len(text_items),
            multimodal_item_count=len(multimodal_items),
            visually_recovered_count=sum(
                item.visually_recovered for item in multimodal_items
            ),
            agreement_count=agreement_count,
            difference_count=difference_count,
            items=comparisons,
        )

    def _compare_pair(
        self,
        key: tuple[int, str, str],
        text_item: ExtractedItem | None,
        multimodal_item: ExtractedItem | None,
    ) -> ComparisonItem:
        """Compare one possible text and multimodal item pair."""
        page_number, category, field_name = key

        if text_item is None and multimodal_item is not None:
            status = "multimodal_only"
            explanation = (
                "The multimodal method recovered information that the "
                "embedded PDF text extraction did not return."
            )
        elif text_item is not None and multimodal_item is None:
            status = "text_only"
            explanation = (
                "The text-only method returned this field, but the "
                "multimodal method did not."
            )
        elif self._normalize(text_item.value) == self._normalize(
            multimodal_item.value
        ):
            status = "agreement"
            explanation = (
                "Both extraction methods returned the same normalized value."
            )
        else:
            status = "different_value"
            explanation = (
                "Both methods found the field but returned different values."
            )

        return ComparisonItem(
            page_number=page_number,
            category=category,
            field_name=field_name,
            text_only_value=(
                text_item.value if text_item is not None else None
            ),
            multimodal_value=(
                multimodal_item.value
                if multimodal_item is not None
                else None
            ),
            text_only_confidence=(
                text_item.confidence if text_item is not None else None
            ),
            multimodal_confidence=(
                multimodal_item.confidence
                if multimodal_item is not None
                else None
            ),
            status=status,
            explanation=explanation,
        )

    @staticmethod
    def _group_items(
        items: list[ExtractedItem],
    ) -> dict[tuple[int, str, str], list[ExtractedItem]]:
        """Group items by their logical comparison key."""
        groups: defaultdict[
            tuple[int, str, str],
            list[ExtractedItem],
        ] = defaultdict(list)

        for item in items:
            key = (
                item.page_number,
                item.category.value,
                item.field_name.strip().lower(),
            )
            groups[key].append(item)

        return dict(groups)

    @staticmethod
    def _normalize(value: object) -> str:
        """Normalize scalar or structured values for comparison."""
        if isinstance(value, str):
            return " ".join(value.lower().split())

        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        ).lower()