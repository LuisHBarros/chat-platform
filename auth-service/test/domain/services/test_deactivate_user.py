from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password
from app.domain.services import DeactivateUser
from test.domain.fake_repositories import FakeUserRepository


@pytest.mark.asyncio
async def test_deactivate_user():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)
    await user_repo.save(user)

    service = DeactivateUser(user_repo)
    deactivated = await service.execute(user)

    assert deactivated.is_active is False
    saved = await user_repo.get_by_id(user.id)
    assert saved.is_active is False
