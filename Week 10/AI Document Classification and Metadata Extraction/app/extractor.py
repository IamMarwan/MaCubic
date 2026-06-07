import re


FIELD_PATTERNS = {
    "document_title": r"Document Title\s*:\s*(.+)",
    "revision_number": r"Revision Number\s*:\s*(.+)",
    "project_name": r"Project Name\s*:\s*(.+)",
    "contractor": r"Contractor\s*:\s*(.+)",
    "consultant": r"Consultant\s*:\s*(.+)",
    "submission_date": r"Submission Date\s*:\s*(.+)",
    "discipline": r"Discipline\s*:\s*(.+)"
}


def extract_metadata(text: str):
    metadata = {}

    for field, pattern in FIELD_PATTERNS.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        metadata[field] = (
            match.group(1).strip()
            if match
            else None
        )

    return metadata