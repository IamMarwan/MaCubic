from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "CubicDocs AI"
    assert payload["version"] == "1.0.0"


def test_readiness_endpoint() -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["database"] == "connected"