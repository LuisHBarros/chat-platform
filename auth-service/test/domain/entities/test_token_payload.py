from datetime import datetime, timezone
from uuid import uuid4
from app.domain.entities import TokenPayload, IssuedToken


def test_token_payload_creation():
    user_id = uuid4()
    jti = uuid4()
    now = datetime.now(timezone.utc)

    payload = TokenPayload(
        user_id=user_id,
        jti=jti,
        expires_at=now,
        token_type="access",
    )

    assert payload.user_id == user_id
    assert payload.jti == jti
    assert payload.token_type == "access"


def test_issued_token_creation():
    jti = uuid4()
    now = datetime.now(timezone.utc)

    issued = IssuedToken(
        token="jwt_string",
        jti=jti,
        expires_at=now,
        token_type="refresh",
    )

    assert issued.token == "jwt_string"
    assert issued.token_type == "refresh"
