import re
import uuid
from collections import Counter
from pathlib import Path

from docx import Document as WordDocument
from fastapi import UploadFile
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE = 10 * 1024 * 1024

STOP_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "before",
    "being",
    "between",
    "both",
    "but",
    "can",
    "could",
    "document",
    "each",
    "for",
    "from",
    "have",
    "into",
    "more",
    "most",
    "not",
    "only",
    "other",
    "our",
    "that",
    "the",
    "their",
    "there",
    "these",
    "they",
    "this",
    "through",
    "under",
    "using",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "will",
    "with",
    "would",
    "your",
}


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name
    safe_name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        safe_name,
    )

    return safe_name or "document"


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))

        raise ValueError(
            f"Unsupported file type. Allowed types: {allowed}"
        )

    return extension


def extract_text(file_path: Path, extension: str) -> str:
    try:
        if extension in {".txt", ".md", ".csv"}:
            return file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        if extension == ".pdf":
            reader = PdfReader(str(file_path))

            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        if extension == ".docx":
            document = WordDocument(str(file_path))

            return "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

    except Exception:
        return ""

    return ""


def generate_summary(text: str) -> str:
    clean_text = " ".join(text.split())

    if not clean_text:
        return (
            "Document uploaded successfully. "
            "No readable text was detected."
        )

    if len(clean_text) <= 350:
        return clean_text

    return clean_text[:347].rstrip() + "..."


def generate_keywords(text: str) -> str:
    words = re.findall(
        r"[A-Za-z]{4,}",
        text.lower(),
    )

    filtered_words = [
        word
        for word in words
        if word not in STOP_WORDS
    ]

    common_words = Counter(filtered_words).most_common(8)

    if not common_words:
        return "No keywords detected"

    return ", ".join(
        word
        for word, _ in common_words
    )


async def save_and_analyze_upload(
    upload: UploadFile,
    upload_directory: Path,
) -> dict:
    if not upload.filename:
        raise ValueError("A file name is required.")

    extension = validate_extension(upload.filename)
    original_name = sanitize_filename(upload.filename)
    content = await upload.read()

    if not content:
        raise ValueError("The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError(
            "The file exceeds the 10 MB size limit."
        )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = upload_directory / stored_name

    file_path.write_bytes(content)

    text = extract_text(
        file_path,
        extension,
    )

    return {
        "original_name": original_name,
        "stored_name": stored_name,
        "file_type": extension.lstrip(".").upper(),
        "file_size": len(content),
        "summary": generate_summary(text),
        "keywords": generate_keywords(text),
        "status": "Processed",
    }


def format_file_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    return f"{size / (1024 * 1024):.1f} MB"
