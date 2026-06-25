import re
from pathlib import Path
from typing import List

from config import MAX_FILE_SIZE_BYTES, REQUIRED_FIELDS, SUPPORTED_EXTENSIONS
from validator.models import ValidationIssue


class ValidationRules:
    def validate_file_type(self, file_path: Path) -> List[ValidationIssue]:
        issues = []

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            issues.append(
                ValidationIssue(
                    rule_id="FILE_TYPE_001",
                    severity="critical",
                    message=f"Unsupported file type: {file_path.suffix}",
                    recommendation="Upload a PDF, DOCX, or TXT document."
                )
            )

        return issues

    def validate_file_size(self, file_path: Path) -> List[ValidationIssue]:
        issues = []

        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            issues.append(
                ValidationIssue(
                    rule_id="FILE_SIZE_001",
                    severity="critical",
                    message="File size exceeds the allowed limit.",
                    recommendation="Compress the file or upload a smaller document."
                )
            )

        return issues

    def validate_empty_document(self, text: str) -> List[ValidationIssue]:
        issues = []

        if not text.strip():
            issues.append(
                ValidationIssue(
                    rule_id="CONTENT_001",
                    severity="critical",
                    message="The document appears to be empty.",
                    recommendation="Upload a document with readable text content."
                )
            )

        return issues

    def validate_minimum_length(self, text: str) -> List[ValidationIssue]:
        issues = []

        words = text.split()

        if 0 < len(words) < 50:
            issues.append(
                ValidationIssue(
                    rule_id="CONTENT_002",
                    severity="warning",
                    message="The document is very short.",
                    recommendation="Review the document to confirm that no sections are missing."
                )
            )

        return issues

    def validate_required_fields(self, text: str) -> List[ValidationIssue]:
        issues = []
        lower_text = text.lower()

        for field in REQUIRED_FIELDS:
            if field not in lower_text:
                issues.append(
                    ValidationIssue(
                        rule_id=f"FIELD_{field.upper()}_001",
                        severity="warning",
                        message=f"Missing required field: {field}",
                        recommendation=f"Add the missing {field} field before submission."
                    )
                )

        return issues

    def validate_date_presence(self, text: str) -> List[ValidationIssue]:
        issues = []

        date_patterns = [
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            r"\b\d{1,2}-\d{1,2}-\d{4}\b",
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
            r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b",
        ]

        has_date = any(re.search(pattern, text) for pattern in date_patterns)

        if not has_date:
            issues.append(
                ValidationIssue(
                    rule_id="DATE_001",
                    severity="warning",
                    message="No clear date was detected in the document.",
                    recommendation="Add a valid submission date or document date."
                )
            )

        return issues

    def validate_signature_presence(self, text: str) -> List[ValidationIssue]:
        issues = []

        signature_keywords = [
            "signature",
            "signed by",
            "approved by",
            "authorized by",
            "stamp"
        ]

        lower_text = text.lower()

        has_signature = any(keyword in lower_text for keyword in signature_keywords)

        if not has_signature:
            issues.append(
                ValidationIssue(
                    rule_id="SIGNATURE_001",
                    severity="warning",
                    message="No signature or approval section was detected.",
                    recommendation="Add a signature, approval, or authorization section."
                )
            )

        return issues

    def validate_common_sections(self, text: str) -> List[ValidationIssue]:
        issues = []

        common_sections = [
            "introduction",
            "scope",
            "conclusion"
        ]

        lower_text = text.lower()

        missing_sections = [
            section for section in common_sections
            if section not in lower_text
        ]

        if len(missing_sections) >= 2:
            issues.append(
                ValidationIssue(
                    rule_id="SECTION_001",
                    severity="info",
                    message=f"Several common sections are missing: {', '.join(missing_sections)}",
                    recommendation="Consider adding standard sections such as introduction, scope, and conclusion."
                )
            )

        return issues