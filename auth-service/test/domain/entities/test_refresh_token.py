from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.entities import RefreshToken


def test_refresh_token_creation_and_activity():
    now = datetime.now(UTC)
    user_id = uuid4()
    jti = uuid4()
    expires_at = now + timedelta(days=7)

    token = RefreshToken.create(user_id, jti, expires_at, now)

    assert token.id is not None
    assert token.user_id == user_id
    assert token.jti == jti
    assert token.revoked_at is None
    assert token.is_active(now) is True


def test_refresh_token_expiration():
    now = datetime.now(UTC)
    user_id = uuid4()
    jti = uuid4()
    past = now - timedelta(days=1)

    token = RefreshToken.create(user_id, jti, past, past)

    assert token.is_active(now) is False


def test_refresh_token_revocation():
    now = datetime.now(UTC)
    user_id = uuid4()
    jti = uuid4()
    expires_at = now + timedelta(days=7)

    token = RefreshToken.create(user_id, jti, expires_at, now)
    revoked = token.revoke(now)

    assert revoked.revoked_at == now
    assert revoked.is_active(now) is False

    # Idempotent revocation
    assert revoked.revoke(now) == revoked
