from datetime import UTC, datetime

import pytest

from app.domain.entities import Email, Password, User, Username
from app.domain.exceptions import ValidationError
from app.domain.services import ChangePassword
from test.domain.fake_repositories import FakePasswordHasher, FakeUserRepository


@pytest.mark.asyncio
async def test_change_password_success():
    now = datetime.now(UTC)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    user = User.create(Email("user@example.com"), Username("user123"), Password("old_hash"), now)
    await user_repo.save(user)

    service = ChangePassword(user_repo, hasher)
    updated = await service.execute(user, "new_secret_123")

    assert updated.password.hashed_value == "hashed_new_secret_123"
    saved = await user_repo.get_by_id(user.id)
    assert saved is not None
    assert saved.password.hashed_value == "hashed_new_secret_123"


@pytest.mark.asyncio
async def test_change_password_empty_raises_error():
    now = datetime.now(UTC)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)

    service = ChangePassword(user_repo, hasher)
    with pytest.raises(ValidationError, match="New password is required"):
        await service.execute(user, "")
