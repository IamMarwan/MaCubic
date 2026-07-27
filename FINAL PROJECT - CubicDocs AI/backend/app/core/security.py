from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a plaintext password."""

    return password_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Compare a plaintext password with a stored password hash."""

    return password_context.verify(
        plain_password,
        hashed_password,
    )


def create_token(
    *,
    subject: str,
    token_type: Literal["access", "refresh"],
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        "exp": expires_at,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        additional_claims=additional_claims,
    )


def create_refresh_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        additional_claims=additional_claims,
    )


def decode_token(
    token: str,
    expected_type: Literal["access", "refresh"] | None = None,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError as exc:
        raise AuthenticationError("The supplied token is invalid or expired.") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthenticationError("The supplied token type is not valid for this action.")

    subject = payload.get("sub")

    if not subject:
        raise AuthenticationError("The token does not contain a valid subject.")

    return payload