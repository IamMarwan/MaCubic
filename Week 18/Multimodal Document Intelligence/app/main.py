"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.core.logging import configure_logging, get_logger
from app.core.settings import get_settings


settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare application resources during startup."""
    configure_logging()
    settings.create_directories()
    logger.info(
        "Starting %s with vision provider '%s'",
        settings.app_name,
        settings.vision_provider,
    )
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Standalone service for visual and textual analysis of complex PDF "
        "documents, including construction drawings, title blocks, tables, "
        "notes, stamps, revisions, symbols, and annotations."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Return basic service navigation information."""
    return {
        "service": settings.app_name,
        "version": __version__,
        "documentation": "/docs",
        "health": "/api/v1/health",
    }