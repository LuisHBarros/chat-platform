from datetime import UTC, datetime

import pytest

from app.domain.entities import Email, Password, User, Username
from app.domain.services import ActivateUser
from test.domain.fake_repositories import FakeUserRepository


@pytest.mark.asyncio
async def test_activate_user():
    now = datetime.now(UTC)
    user_repo = FakeUserRepository()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now).deactivate(now)
    await user_repo.save(user)

    service = ActivateUser(user_repo)
    activated = await service.execute(user)

    assert activated.is_active is True
    saved = await user_repo.get_by_id(user.id)
    assert saved is not None
    assert saved.is_active is True
