from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text_from_docx(path: str):

    document = Document(path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def extract_text_from_pdf(path: str):

    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        pages.append(
            page.extract_text() or ""
        )

    return "\n".join(pages)


def extract_text(path: str):

    extension = Path(path).suffix.lower()

    if extension == ".docx":
        return extract_text_from_docx(path)

    if extension == ".pdf":
        return extract_text_from_pdf(path)

    raise ValueError(
        "Only PDF and DOCX files are supported."
    )