import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.telemetry import record_http_request

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add a request ID, timing information, logging, and metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        started_at = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration = time.perf_counter() - started_at

            logger.exception(
                "Unhandled request error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_seconds=round(duration, 6),
            )
            raise

        duration = time.perf_counter() - started_at

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.6f}"

        record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_seconds=duration,
        )

        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_seconds=round(duration, 6),
        )

        return response