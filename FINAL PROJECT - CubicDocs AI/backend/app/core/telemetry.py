from prometheus_client import Counter, Histogram

from app.core.config import settings

HTTP_REQUEST_COUNT = Counter(
    "cubicdocs_http_requests_total",
    "Total number of HTTP requests.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "cubicdocs_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    ["method", "path"],
)

DOCUMENT_PROCESSING_COUNT = Counter(
    "cubicdocs_document_processing_total",
    "Number of processed documents.",
    ["status"],
)


def record_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    if not settings.enable_metrics:
        return

    normalized_path = normalize_metric_path(path)

    HTTP_REQUEST_COUNT.labels(
        method=method,
        path=normalized_path,
        status_code=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        path=normalized_path,
    ).observe(duration_seconds)


def record_document_processing(status: str) -> None:
    if settings.enable_metrics:
        DOCUMENT_PROCESSING_COUNT.labels(status=status).inc()


def normalize_metric_path(path: str) -> str:
    """
    Reduce excessive metric-cardinality for numeric identifiers.

    Example:
        /api/v1/documents/42 -> /api/v1/documents/{id}
    """

    parts = path.strip("/").split("/")
    normalized_parts = [
        "{id}" if part.isdigit() else part
        for part in parts
    ]

    return "/" + "/".join(normalized_parts)