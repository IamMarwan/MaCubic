import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.classifier import classify_document
from app.extractor import extract_metadata
from app.file_parser import extract_text
from app.models import ClassificationResult


app = FastAPI(
    title="AI Document Control Assistant",
    description="Classifies construction documents and extracts metadata.",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "AI Document Control Assistant"
    }


@app.post("/upload", response_model=ClassificationResult)
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        text = extract_text(temp_path)

        document_type, confidence_score = classify_document(text)
        metadata = extract_metadata(text)

        return {
            "filename": file.filename,
            "document_type": document_type,
            "confidence_score": confidence_score,
            "metadata": metadata
        }

    finally:
        os.remove(temp_path)