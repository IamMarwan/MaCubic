import re
from typing import Iterable

from app.models import Document, DocumentRelationship


class RelationshipEngine:
    """
    Detects simple relationships between construction project documents.

    The engine uses document numbers and document types to connect:
    - RFIs to drawings/specifications
    - Meeting minutes to action items and referenced documents
    - Any document to another document when its document number is mentioned
    """

    def build_relationships(
        self,
        documents: Iterable[Document],
    ) -> list[DocumentRelationship]:
        document_list = list(documents)
        relationships: list[DocumentRelationship] = []

        for source in document_list:
            for target in document_list:
                if source.id == target.id:
                    continue

                relationship = self._detect_relationship(source, target)

                if relationship:
                    relationships.append(relationship)

        return relationships

    def _detect_relationship(
        self,
        source: Document,
        target: Document,
    ) -> DocumentRelationship | None:
        content = source.content.lower()
        target_number = target.document_number.lower()

        if not self._contains_reference(content, target_number):
            return None

        relationship_type = self._classify_relationship(source, target)
        explanation = (
            f"{source.document_number} references {target.document_number} "
            f"inside its document content."
        )

        return DocumentRelationship(
            source_document_id=source.id,
            target_document_id=target.id,
            relationship_type=relationship_type,
            confidence_score=95,
            explanation=explanation,
        )

    def _contains_reference(self, content: str, document_number: str) -> bool:
        pattern = re.escape(document_number.lower())
        return re.search(pattern, content) is not None

    def _classify_relationship(
        self,
        source: Document,
        target: Document,
    ) -> str:
        source_type = source.document_type.lower()
        target_type = target.document_type.lower()

        if source_type == "rfi" and target_type == "drawing":
            return "RFI_REFERENCES_DRAWING"

        if source_type == "rfi" and target_type == "specification":
            return "RFI_REFERENCES_SPECIFICATION"

        if source_type == "meeting_minutes" and target_type == "action_item":
            return "MEETING_MINUTES_ASSIGN_ACTION_ITEM"

        if source_type == "meeting_minutes":
            return "MEETING_MINUTES_REFERENCES_DOCUMENT"

        return "REFERENCES"