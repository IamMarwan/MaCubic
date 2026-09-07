"""HTTP endpoints for document extraction and comparison."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app import __version__
from app.core.settings import get_settings
from app.models.schemas import (
    ComparisonResponse,
    DocumentExtractionResponse,
    HealthResponse,
)
from app.services.document_service import DocumentIntelligenceService
from app.services.openai_vision_provider import VisionProviderError
from app.services.pdf_processor import PDFProcessingError


router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Return application and provider health information."""
    return HealthResponse(
        status="healthy",
        application=settings.app_name,
        version=__version__,
        vision_provider=settings.vision_provider,
        model=(
            settings.openai_model
            if settings.vision_provider == "openai"
            else "deterministic-visual-analyzer-v1"
        ),
    )


@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
    tags=["Document Intelligence"],
)
async def extract_document(
    file: UploadFile = File(...),
) -> DocumentExtractionResponse:
    """Return structured multimodal extraction for an uploaded PDF."""
    result = await _analyze_upload(file)
    return result.multimodal


@router.post(
    "/compare",
    response_model=ComparisonResponse,
    tags=["Document Intelligence"],
)
async def compare_document(
    file: UploadFile = File(...),
) -> ComparisonResponse:
    """Compare text-only extraction against multimodal extraction."""
    result = await _analyze_upload(file)
    return result.comparison


@router.post(
    "/analyze",
    tags=["Document Intelligence"],
)
async def analyze_document(
    file: UploadFile = File(...),
) -> dict[str, object]:
    """Return text-only, multimodal, and comparison results together."""
    result = await _analyze_upload(file)

    return {
        "text_only": result.text_only.model_dump(mode="json"),
        "multimodal": result.multimodal.model_dump(mode="json"),
        "comparison": result.comparison.model_dump(mode="json"),
    }


async def _analyze_upload(file: UploadFile):
    """Read and analyze one uploaded PDF with consistent error handling."""
    filename = file.filename or "uploaded.pdf"

    if file.content_type not in {
        "application/pdf",
        "application/octet-stream",
        None,
    }:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF uploads are supported.",
        )

    try:
        pdf_bytes = await file.read()
        service = DocumentIntelligenceService()
        return await service.analyze(
            pdf_bytes=pdf_bytes,
            filename=filename,
        )
    except PDFProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except VisionProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()