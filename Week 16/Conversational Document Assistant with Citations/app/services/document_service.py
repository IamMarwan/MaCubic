from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.utils.text_processing import split_text_into_chunks


def read_uploaded_file(file: UploadFile) -> str:
    content = file.file.read()

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def save_document(db: Session, file: UploadFile) -> Document:
    text = read_uploaded_file(file)
    chunks = split_text_into_chunks(text)

    document = Document(filename=file.filename)
    db.add(document)
    db.commit()
    db.refresh(document)

    for index, chunk_text in enumerate(chunks, start=1):
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk_text
        )
        db.add(chunk)

    db.commit()
    db.refresh(document)

    return document