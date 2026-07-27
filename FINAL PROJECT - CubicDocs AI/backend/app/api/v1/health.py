from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(HealthResponse):
    database: str


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
def liveness_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
)
def readiness_check(
    database: Session = Depends(get_db),
) -> ReadinessResponse:
    database.execute(text("SELECT 1"))

    return ReadinessResponse(
        status="ready",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
        database="connected",
    )