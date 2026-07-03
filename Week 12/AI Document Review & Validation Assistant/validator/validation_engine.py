from pathlib import Path
from typing import List

from config import FAIL, PASS, WARNING
from validator.file_utils import extract_text, file_size
from validator.models import ValidationIssue
from validator.validation_rules import ValidationRules


class ValidationEngine:
    def __init__(self):
        self.rules = ValidationRules()

    def run_validation(self, file_path: Path) -> List[ValidationIssue]:
        issues = []

        issues.extend(self.rules.validate_file_type(file_path))
        issues.extend(self.rules.validate_file_size(file_path))

        if self.has_critical_issue(issues):
            return issues

        text = extract_text(file_path)

        issues.extend(self.rules.validate_empty_document(text))
        issues.extend(self.rules.validate_minimum_length(text))
        issues.extend(self.rules.validate_required_fields(text))
        issues.extend(self.rules.validate_date_presence(text))
        issues.extend(self.rules.validate_signature_presence(text))
        issues.extend(self.rules.validate_common_sections(text))

        return issues

    def calculate_score(self, issues: List[ValidationIssue]) -> float:
        score = 100.0

        for issue in issues:
            if issue.severity == "critical":
                score -= 35
            elif issue.severity == "warning":
                score -= 12
            elif issue.severity == "info":
                score -= 5

        return max(score, 0.0)

    def determine_status(self, issues: List[ValidationIssue]) -> str:
        if any(issue.severity == "critical" for issue in issues):
            return FAIL

        if any(issue.severity == "warning" for issue in issues):
            return WARNING

        return PASS

    def has_critical_issue(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.severity == "critical" for issue in issues)

    def get_file_metadata(self, file_path: Path) -> dict:
        return {
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_size_bytes": file_size(file_path),
            "file_path": str(file_path),
        }