import hashlib
from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document


def file_hash(file_path: Path) -> str:
    sha = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)

            if not chunk:
                break

            sha.update(chunk)

    return sha.hexdigest()


def read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def read_docx(file_path: Path) -> str:
    doc = Document(str(file_path))

    text = []

    for paragraph in doc.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


def read_txt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return read_pdf(file_path)

    if extension == ".docx":
        return read_docx(file_path)

    if extension == ".txt":
        return read_txt(file_path)

    raise ValueError(f"Unsupported file type: {extension}")


def file_size(file_path: Path) -> int:
    return file_path.stat().st_size