from pathlib import Path

from config import UPLOAD_DIR
from validator.duplicate_detector import DuplicateDetector
from validator.file_utils import extract_text
from validator.models import ReviewReport
from validator.summarizer import DocumentSummarizer
from validator.validation_engine import ValidationEngine


class DocumentReviewer:
    def __init__(self):
        self.validation_engine = ValidationEngine()
        self.duplicate_detector = DuplicateDetector(UPLOAD_DIR)
        self.summarizer = DocumentSummarizer()

    def review_document(self, file_path: Path) -> ReviewReport:
        issues = self.validation_engine.run_validation(file_path)
        duplicate_matches = self.duplicate_detector.find_duplicates(file_path)

        text = self._safe_extract_text(file_path)
        title = self._detect_title(text, file_path.name)

        summary = self.summarizer.summarize(text, title)

        warnings = self._build_warnings(issues, duplicate_matches)
        recommendations = self._build_recommendations(issues, duplicate_matches)

        validation_score = self.validation_engine.calculate_score(issues)

        if duplicate_matches:
            validation_score = max(validation_score - 15, 0)

        status = self.validation_engine.determine_status(issues)

        if duplicate_matches and status == "PASS":
            status = "WARNING"

        metadata = self.validation_engine.get_file_metadata(file_path)

        return ReviewReport(
            file_name=file_path.name,
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
            validation_score=validation_score,
            status=status,
            issues=issues,
            duplicate_matches=duplicate_matches,
            summary=summary,
            warnings=warnings,
            recommendations=recommendations,
            metadata=metadata
        )

    def _safe_extract_text(self, file_path: Path) -> str:
        try:
            return extract_text(file_path)
        except Exception:
            return ""

    def _detect_title(self, text: str, fallback: str) -> str:
        for line in text.splitlines():
            cleaned = line.strip()

            if cleaned:
                return cleaned[:120]

        return fallback

    def _build_warnings(self, issues, duplicate_matches) -> list:
        warnings = []

        for issue in issues:
            if issue.severity in ["critical", "warning"]:
                warnings.append(issue.message)

        for duplicate in duplicate_matches:
            warnings.append(
                f"Possible duplicate detected: {duplicate.matched_file} "
                f"({duplicate.similarity_score}%)"
            )

        if not warnings:
            warnings.append("No major warnings detected.")

        return warnings

    def _build_recommendations(self, issues, duplicate_matches) -> list:
        recommendations = []

        for issue in issues:
            recommendations.append(issue.recommendation)

        if duplicate_matches:
            recommendations.append(
                "Review duplicate matches before approving this submission."
            )

        if not recommendations:
            recommendations.append(
                "Document is ready for submission."
            )

        return list(dict.fromkeys(recommendations))