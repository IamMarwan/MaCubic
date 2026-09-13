"""Bounded TXT/MD/PDF input. No OCR and no execution of document content."""

import hashlib
import io
from pathlib import PurePosixPath

from app.config import Settings
from app.models import Document, InputError


def read_document(filename: str, content: bytes, settings: Settings) -> Document:
    if not isinstance(filename, str) or not filename.strip():
        raise InputError("A filename is required.")
    filename = PurePosixPath(filename.replace("\\", "/")).name
    if len(filename) > 180 or any(ord(c) < 32 for c in filename):
        raise InputError("Invalid filename.")
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise InputError("Supported formats: .txt, .md, .pdf.")
    if not content:
        raise InputError("The document is empty.")
    if len(content) > settings.max_upload_bytes:
        raise InputError("The document exceeds the 10 MB upload limit.")
    pages = 1
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise InputError("The uploaded file is not a valid PDF.")
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise InputError("Install requirements.txt to enable PDF uploads.") from exc
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise InputError("Encrypted PDFs are not supported.")
            pages = len(reader.pages)
            if not 1 <= pages <= settings.max_pages:
                raise InputError(f"PDF must contain 1 to {settings.max_pages} pages.")
            extracted = []
            for number, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    raise InputError(f"PDF page {number} has no readable text; OCR is required.")
                extracted.append(page_text)
                if sum(len(t) for t in extracted) > settings.max_text_chars:
                    raise InputError("Document text exceeds the character limit.")
            text = "\n".join(extracted)
        except InputError:
            raise
        except Exception as exc:
            raise InputError("PDF could not be parsed.") from exc
    else:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InputError("Text files must use UTF-8 encoding.") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\x00" in text or not text.strip():
        raise InputError("The file contains no usable text or contains binary data.")
    if len(text) > settings.max_text_chars:
        raise InputError("Document text exceeds the character limit.")
    return Document(filename, text, hashlib.sha256(content).hexdigest(), pages)
