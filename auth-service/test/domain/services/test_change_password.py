from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password
from app.domain.exceptions import ValidationError
from app.domain.services import ChangePassword
from test.domain.fake_repositories import FakePasswordHasher, FakeUserRepository


@pytest.mark.asyncio
async def test_change_password_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    user = User.create(Email("user@example.com"), Username("user123"), Password("old_hash"), now)
    await user_repo.save(user)

    service = ChangePassword(user_repo, hasher)
    updated = await service.execute(user, "new_secret_123")

    assert updated.password.hashed_value == "hashed_new_secret_123"
    saved = await user_repo.get_by_id(user.id)
    assert saved.password.hashed_value == "hashed_new_secret_123"


@pytest.mark.asyncio
async def test_change_password_empty_raises_error():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)

    service = ChangePassword(user_repo, hasher)
    with pytest.raises(ValidationError, match="New password is required"):
        await service.execute(user, "")
