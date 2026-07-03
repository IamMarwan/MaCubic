from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from validator.summarizer import DocumentSummarizer


def test_summary_generation_returns_text():
    text = """
    Cubic Engineering Consultancy prepared this project submission document
    to support review and validation before final submission.

    The document includes scope details, technical review notes, project
    coordination information, and approval recommendations.

    The validation assistant should generate warnings, recommendations,
    and a summary for each uploaded document.
    """

    summarizer = DocumentSummarizer()
    result = summarizer.summarize(text, "Test Document")

    assert result.title == "Test Document"
    assert result.word_count > 0
    assert result.character_count > 0
    assert len(result.summary) > 0
    assert isinstance(result.keywords, list)