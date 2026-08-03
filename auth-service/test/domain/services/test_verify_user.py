from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password
from app.domain.services import VerifyUser
from test.domain.fake_repositories import FakeUserRepository


@pytest.mark.asyncio
async def test_verify_user_service():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)
    await user_repo.save(user)

    verifier = VerifyUser(user_repo)
    verified = await verifier.execute(user)

    assert verified.is_verified is True
    saved = await user_repo.get_by_id(user.id)
    assert saved.is_verified is True
