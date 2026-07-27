from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    password = "Strong-Test-Password-123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("incorrect-password", password_hash) is False


def test_access_token_creation_and_decoding() -> None:
    token = create_access_token(
        subject="user-123",
        additional_claims={"role": "administrator"},
    )

    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["role"] == "administrator"