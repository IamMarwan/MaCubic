from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import initialize_database
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.ensure_storage_directories()
    initialize_database()

    logger.info(
        "Application started",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

    yield

    logger.info(
        "Application stopped",
        application=settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-ready AI document control and intelligence platform "
        "for engineering and project teams."
    ),
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)

install_exception_handlers(app)

app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


@app.get(
    "/",
    tags=["Application"],
)
def root() -> JSONResponse:
    return JSONResponse(
        content={
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "status": "running",
            "documentation": "/docs",
            "health": f"{settings.api_v1_prefix}/health/live",
        }
    )


@app.get(
    "/metrics",
    include_in_schema=False,
)
def metrics() -> Response:
    if not settings.enable_metrics:
        return Response(
            content="Metrics are disabled.",
            status_code=404,
            media_type="text/plain",
        )

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )