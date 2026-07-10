import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


FIELD_PATTERNS = {
    "document_number": r"(?:Document\s*(?:No\.?|Number)|Doc\s*No\.?)\s*[:\-]\s*([A-Z0-9\-_/]+)",
    "revision": r"(?:Revision|Rev\.?)\s*[:\-]\s*([A-Z0-9]+)",
    "approval_status": r"(?:Approval\s*Status|Status)\s*[:\-]\s*([A-Za-z ]+)",
    "date": r"(?:Date|Submission\s*Date|Issue\s*Date)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}/[0-9]{2}/[0-9]{4})",
    "prepared_by": r"Prepared\s*By\s*[:\-]\s*([A-Za-z .,&]+)",
    "checked_by": r"Checked\s*By\s*[:\-]\s*([A-Za-z .,&]+)",
    "approved_by": r"Approved\s*By\s*[:\-]\s*([A-Za-z .,&]+)",
    "discipline": r"Discipline\s*[:\-]\s*([A-Za-z ]+)",
    "project_name": r"Project\s*Name\s*[:\-]\s*(.+)",
}


def extract_text(file_path):
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    raise ValueError(f"Unsupported file type: {suffix}")


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_metadata(text):
    metadata = {}

    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            metadata[key] = match.group(1).strip()

    return metadata


def detect_document_type(text, rules):
    lowered = text.lower()
    first_lines = "\n".join(text.lower().splitlines()[:5])

    best_type = "unknown"
    best_score = 0

    for document_type, rule_config in rules.get("document_types", {}).items():
        keywords = rule_config.get("keywords", [])
        score = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()

            if keyword_lower in lowered:
                score += 1

            if keyword_lower in first_lines:
                score += 5

        if document_type.replace("_", " ") in first_lines:
            score += 8

        if score > best_score:
            best_score = score
            best_type = document_type

    return best_type