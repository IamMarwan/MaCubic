import base64
import hashlib
import hmac
import os
from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer

PBKDF2_ITERATIONS = 390000


def hash_password(password: str) -> str:
    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    encoded_salt = base64.b64encode(salt).decode("utf-8")
    encoded_hash = base64.b64encode(password_hash).decode("utf-8")

    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{encoded_salt}${encoded_hash}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, encoded_salt, encoded_hash = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.b64decode(encoded_salt)
        expected_hash = base64.b64decode(encoded_hash)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


def get_serializer(secret_key: str) -> URLSafeSerializer:
    return URLSafeSerializer(
        secret_key,
        salt="week17-session",
    )


def create_session_token(secret_key: str, user_id: int) -> str:
    serializer = get_serializer(secret_key)
    return serializer.dumps({"user_id": user_id})


def read_session_token(
    secret_key: str,
    token: str | None,
) -> dict[str, Any] | None:
    if not token:
        return None

    serializer = get_serializer(secret_key)

    try:
        data = serializer.loads(token)
    except BadSignature:
        return None

    if not isinstance(data, dict):
        return None

    if "user_id" not in data:
        return None

    return data
