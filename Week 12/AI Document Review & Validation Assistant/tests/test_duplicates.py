from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from validator.duplicate_detector import DuplicateDetector


def test_exact_duplicate_is_detected(tmp_path):
    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"

    content = """
    Title: Project Report
    Author: Marwan
    Date: 25 June 2026

    Introduction:
    This document contains a complete project report.

    Scope:
    The scope includes validation, review, and submission checking.

    Conclusion:
    This document is complete.

    Signature:
    Approved by Cubic Engineering Consultancy.
    """

    first_file.write_text(content, encoding="utf-8")
    second_file.write_text(content, encoding="utf-8")

    detector = DuplicateDetector(tmp_path)
    matches = detector.find_duplicates(second_file)

    assert len(matches) >= 1
    assert matches[0].similarity_score == 100


def test_different_document_is_not_exact_duplicate(tmp_path):
    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"

    first_file.write_text(
        "This is the first project report about site inspection.",
        encoding="utf-8"
    )

    second_file.write_text(
        "This is a completely different financial summary.",
        encoding="utf-8"
    )

    detector = DuplicateDetector(tmp_path)
    matches = detector.find_duplicates(second_file)

    exact_matches = [
        match for match in matches
        if match.match_type == "Exact hash match"
    ]

    assert len(exact_matches) == 0