import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///./data/test_document_control.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from app.main import app
from app.security import hash_password, verify_password


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == "1.0.0"


def test_home_page():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "AI Document Control Assistant" in response.text


def test_password_hashing():
    password = "SecurePassword123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_registration():
    unique_email = f"user-{uuid.uuid4().hex}@example.com"

    with TestClient(app) as client:
        response = client.post(
            "/register",
            data={
                "full_name": "Test User",
                "email": unique_email,
                "password": "Password123",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
