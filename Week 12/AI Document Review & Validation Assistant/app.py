import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from config import REPORT_DIR, UPLOAD_DIR, SUPPORTED_EXTENSIONS
from validator.reviewer import DocumentReviewer
from validator.report_generator import ReportGenerator


app = FastAPI(
    title="AI Document Review & Validation Assistant",
    description="Reviews uploaded documents, validates required information, detects duplicates, summarizes content, and generates review reports.",
    version="1.0.0"
)

reviewer = DocumentReviewer()
report_generator = ReportGenerator()


@app.get("/")
def home():
    return {
        "message": "AI Document Review & Validation Assistant is running.",
        "supported_extensions": list(SUPPORTED_EXTENSIONS),
        "available_endpoints": [
            "POST /review",
            "GET /reports",
            "GET /download-report/{file_name}"
        ]
    }


@app.post("/review")
async def review_document(file: UploadFile = File(...)):
    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}. Supported types: {SUPPORTED_EXTENSIONS}"
        )

    saved_path = UPLOAD_DIR / original_name

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    report = reviewer.review_document(saved_path)

    json_report_path = report_generator.save_json_report(report, REPORT_DIR)
    pdf_report_path = report_generator.save_pdf_report(report, REPORT_DIR)

    return {
        "message": "Document reviewed successfully.",
        "file_name": report.file_name,
        "status": report.status,
        "validation_score": report.validation_score,
        "warnings": report.warnings,
        "recommendations": report.recommendations,
        "duplicate_matches": [
            duplicate.model_dump()
            for duplicate in report.duplicate_matches
        ],
        "summary": report.summary.model_dump() if report.summary else None,
        "json_report": json_report_path.name,
        "pdf_report": pdf_report_path.name
    }


@app.get("/reports")
def list_reports():
    reports = []

    for report in REPORT_DIR.iterdir():
        if report.is_file():
            reports.append(report.name)

    return {
        "total_reports": len(reports),
        "reports": reports
    }


@app.get("/download-report/{file_name}")
def download_report(file_name: str):
    report_path = REPORT_DIR / file_name

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    return FileResponse(
        path=report_path,
        filename=file_name,
        media_type="application/octet-stream"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )