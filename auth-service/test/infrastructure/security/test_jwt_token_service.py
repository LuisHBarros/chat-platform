from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.domain.exceptions import AuthenticationError
from app.domain.services.token_service import TokenService
from app.infrastructure.security.jwt_token_service import JwtTokenService, PyJWTTokenService


@pytest.fixture
def secret_key() -> str:
    return "super-secret-key-for-testing-jwt-service-at-least-32-bytes-long"


@pytest.fixture
def jwt_service(secret_key: str) -> JwtTokenService:
    return JwtTokenService(
        secret_key=secret_key,
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


def test_jwt_token_service_implements_protocol(jwt_service: JwtTokenService) -> None:
    assert isinstance(jwt_service, TokenService)
    alias_service = PyJWTTokenService(secret_key="super-secret-key-at-least-32-bytes-long")
    assert isinstance(alias_service, TokenService)


def test_create_access_token(jwt_service: JwtTokenService) -> None:
    user_id = uuid4()
    before = datetime.now(UTC)

    issued = jwt_service.create_access_token(user_id)
    after = datetime.now(UTC)

    assert issued.token is not None
    assert isinstance(issued.token, str)
    assert issued.token_type == "access"
    assert issued.jti is not None

    # Check expiration is approximately 15 minutes from now
    expected_expires_min = before + timedelta(minutes=15)
    expected_expires_max = after + timedelta(minutes=15)
    assert expected_expires_min <= issued.expires_at <= expected_expires_max

    # Decode and check payload
    payload = jwt_service.decode(issued.token)
    assert payload.user_id == user_id
    assert payload.jti == issued.jti
    assert payload.token_type == "access"
    assert abs((payload.expires_at - issued.expires_at).total_seconds()) < 2


def test_create_refresh_token(jwt_service: JwtTokenService) -> None:
    user_id = uuid4()
    before = datetime.now(UTC)

    issued = jwt_service.create_refresh_token(user_id)
    after = datetime.now(UTC)

    assert issued.token is not None
    assert issued.token_type == "refresh"
    assert issued.jti is not None

    # Check expiration is approximately 7 days from now
    expected_expires_min = before + timedelta(days=7)
    expected_expires_max = after + timedelta(days=7)
    assert expected_expires_min <= issued.expires_at <= expected_expires_max

    # Decode and check payload
    payload = jwt_service.decode(issued.token)
    assert payload.user_id == user_id
    assert payload.jti == issued.jti
    assert payload.token_type == "refresh"
    assert abs((payload.expires_at - issued.expires_at).total_seconds()) < 2


def test_decode_invalid_signature_raises_authentication_error(
    jwt_service: JwtTokenService,
) -> None:
    user_id = uuid4()
    other_service = JwtTokenService(secret_key="different-super-secret-key-32bytes-long")
    issued = other_service.create_access_token(user_id)

    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        jwt_service.decode(issued.token)


def test_decode_expired_token_raises_authentication_error(secret_key: str) -> None:
    expired_service = JwtTokenService(
        secret_key=secret_key,
        access_token_expire_minutes=-5,  # expired 5 mins ago
    )
    user_id = uuid4()
    issued = expired_service.create_access_token(user_id)

    service = JwtTokenService(secret_key=secret_key)
    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        service.decode(issued.token)


def test_decode_malformed_token_string_raises_authentication_error(
    jwt_service: JwtTokenService,
) -> None:
    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        jwt_service.decode("not.a.valid.jwt.string")


def test_decode_missing_claims_raises_authentication_error(secret_key: str) -> None:
    # Token missing 'sub'
    raw_payload = {
        "jti": str(uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "type": "access",
    }
    token = jwt.encode(raw_payload, secret_key, algorithm="HS256")

    service = JwtTokenService(secret_key=secret_key)
    with pytest.raises(AuthenticationError, match="Malformed token payload"):
        service.decode(token)


def test_decode_invalid_token_type_raises_authentication_error(secret_key: str) -> None:
    raw_payload = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "type": "unsupported_type",
    }
    token = jwt.encode(raw_payload, secret_key, algorithm="HS256")

    service = JwtTokenService(secret_key=secret_key)
    with pytest.raises(AuthenticationError, match="Invalid token type"):
        service.decode(token)


def test_custom_expiration_times() -> None:
    service = JwtTokenService(
        secret_key="super-secret-key-at-least-32-bytes-long",
        access_token_expire_minutes=60,
        refresh_token_expire_days=30,
    )

    user_id = uuid4()

    access_issued = service.create_access_token(user_id)
    refresh_issued = service.create_refresh_token(user_id)

    now = datetime.now(UTC)
    assert abs((access_issued.expires_at - (now + timedelta(minutes=60))).total_seconds()) < 5
    assert abs((refresh_issued.expires_at - (now + timedelta(days=30))).total_seconds()) < 5
