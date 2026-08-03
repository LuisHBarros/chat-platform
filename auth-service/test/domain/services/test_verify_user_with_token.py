from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password, VerificationToken
from app.domain.exceptions import ValidationError
from app.domain.services import VerifyUserWithToken
from test.domain.fake_repositories import FakeUserRepository, FakeVerificationTokenRepository


@pytest.mark.asyncio
async def test_verify_user_with_token_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    token_repo = FakeVerificationTokenRepository()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)
    await user_repo.save(user)

    token_entity, raw_token = VerificationToken.create(user.id, "email_verification", now)
    await token_repo.create(token_entity)

    service = VerifyUserWithToken(user_repo, token_repo)
    verified_user = await service.execute(raw_token)

    assert verified_user.is_verified is True
    saved_user = await user_repo.get_by_id(user.id)
    assert saved_user.is_verified is True

    saved_token = await token_repo.get_by_token(raw_token, "email_verification")
    assert saved_token.used_at is not None


@pytest.mark.asyncio
async def test_verify_user_with_token_invalid_or_expired():
    user_repo = FakeUserRepository()
    token_repo = FakeVerificationTokenRepository()
    service = VerifyUserWithToken(user_repo, token_repo)

    with pytest.raises(ValidationError):
        await service.execute("non_existent_token")
