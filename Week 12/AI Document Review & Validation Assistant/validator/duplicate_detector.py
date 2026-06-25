from pathlib import Path
from typing import List

from rapidfuzz import fuzz

from config import DUPLICATE_THRESHOLD
from validator.file_utils import extract_text, file_hash
from validator.models import DuplicateMatch


class DuplicateDetector:
    def __init__(self, upload_directory: Path):
        self.upload_directory = upload_directory

    def find_duplicates(self, current_file: Path) -> List[DuplicateMatch]:
        matches = []

        if not self.upload_directory.exists():
            return matches

        current_hash = file_hash(current_file)
        current_text = self._safe_extract_text(current_file)

        for existing_file in self.upload_directory.iterdir():
            if not existing_file.is_file():
                continue

            if existing_file.name == current_file.name:
                continue

            hash_score = self._compare_hashes(current_hash, existing_file)

            if hash_score == 100:
                matches.append(
                    DuplicateMatch(
                        matched_file=existing_file.name,
                        similarity_score=100,
                        match_type="Exact hash match"
                    )
                )
                continue

            existing_text = self._safe_extract_text(existing_file)

            if not current_text or not existing_text:
                continue

            text_score = fuzz.token_set_ratio(current_text, existing_text)

            if text_score >= DUPLICATE_THRESHOLD:
                matches.append(
                    DuplicateMatch(
                        matched_file=existing_file.name,
                        similarity_score=round(text_score, 2),
                        match_type="Text similarity match"
                    )
                )

        return matches

    def _compare_hashes(self, current_hash: str, existing_file: Path) -> int:
        try:
            existing_hash = file_hash(existing_file)

            if current_hash == existing_hash:
                return 100

            return 0

        except Exception:
            return 0

    def _safe_extract_text(self, file_path: Path) -> str:
        try:
            return extract_text(file_path)
        except Exception:
            return ""