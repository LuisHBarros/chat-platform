from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.domain.entities import VerificationToken


def test_verification_token_creation():
    now = datetime.now(timezone.utc)
    user_id = uuid4()

    token_entity, raw_token = VerificationToken.create(
        user_id=user_id,
        token_type="email_verification",
        now=now,
        ttl_minutes=60,
    )

    assert token_entity.id is not None
    assert token_entity.user_id == user_id
    assert token_entity.token == raw_token
    assert token_entity.token_type == "email_verification"
    assert token_entity.used_at is None
    assert token_entity.is_valid(now) is True


def test_verification_token_mark_as_used():
    now = datetime.now(timezone.utc)
    token_entity, _ = VerificationToken.create(uuid4(), "password_reset", now)

    used = token_entity.mark_as_used(now)

    assert used.used_at == now
    assert used.is_valid(now) is False
    assert used.mark_as_used(now) == used


def test_verification_token_expiration():
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=2)

    token_entity, _ = VerificationToken.create(uuid4(), "email_verification", past, ttl_minutes=60)

    assert token_entity.is_valid(now) is False
