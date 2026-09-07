"""Integration tests for the FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint() -> None:
    """The root endpoint should provide service navigation."""
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["documentation"] == "/docs"


def test_health_endpoint() -> None:
    """The health endpoint should report the configured provider."""
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["vision_provider"] in {"mock", "openai"}


def test_extract_endpoint(sample_pdf_bytes: bytes) -> None:
    """The API should return structured multimodal extraction."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/extract",
            files={
                "file": (
                    "sample.pdf",
                    sample_pdf_bytes,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sample.pdf"
    assert body["page_count"] == 1
    assert body["provider"] == "mock"
    assert body["total_items"] > 0
    assert body["pages"][0]["page_number"] == 1


def test_compare_endpoint(sample_pdf_bytes: bytes) -> None:
    """The API should identify visually recovered information."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/compare",
            files={
                "file": (
                    "sample.pdf",
                    sample_pdf_bytes,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["text_only_item_count"] > 0
    assert body["multimodal_item_count"] > 0
    assert body["visually_recovered_count"] >= 2


def test_reject_non_pdf_upload() -> None:
    """The API should reject unsupported media types."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/extract",
            files={
                "file": (
                    "notes.txt",
                    b"Not a PDF",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 415