from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password, VerificationToken
from app.domain.exceptions import ValidationError
from app.domain.services import ResetPasswordWithToken
from test.domain.fake_repositories import (
    FakePasswordHasher,
    FakeUserRepository,
    FakeVerificationTokenRepository,
)


@pytest.mark.asyncio
async def test_reset_password_with_token_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    token_repo = FakeVerificationTokenRepository()
    hasher = FakePasswordHasher()

    user = User.create(Email("user@example.com"), Username("user123"), Password("old_hash"), now)
    await user_repo.save(user)

    token_entity, raw_token = VerificationToken.create(user.id, "password_reset", now)
    await token_repo.create(token_entity)

    service = ResetPasswordWithToken(user_repo, token_repo, hasher)
    updated_user = await service.execute(raw_token, "new_secret_123")

    assert updated_user.password.hashed_value == "hashed_new_secret_123"
    saved_user = await user_repo.get_by_id(user.id)
    assert saved_user.password.hashed_value == "hashed_new_secret_123"

    saved_token = await token_repo.get_by_token(raw_token, "password_reset")
    assert saved_token.used_at is not None


@pytest.mark.asyncio
async def test_reset_password_with_empty_inputs():
    service = ResetPasswordWithToken(FakeUserRepository(), FakeVerificationTokenRepository(), FakePasswordHasher())

    with pytest.raises(ValidationError, match="Token is required"):
        await service.execute("", "new_pass")

    with pytest.raises(ValidationError, match="New password is required"):
        await service.execute("valid_token", "")
