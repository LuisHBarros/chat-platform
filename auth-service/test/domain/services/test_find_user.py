from datetime import UTC, datetime

import pytest

from app.domain.entities import Email, Password, User, Username
from app.domain.services import FindUser
from test.domain.fake_repositories import FakeUserRepository


@pytest.mark.asyncio
async def test_find_user_by_id_email_username():
    now = datetime.now(UTC)
    user_repo = FakeUserRepository()

    email = Email("findme@example.com")
    username = Username("findme")
    user = User.create(email, username, Password("hash"), now)
    await user_repo.save(user)

    finder = FindUser(user_repo)

    found_by_id = await finder.by_id(user.id)
    assert found_by_id == user

    found_by_email = await finder.by_email(email)
    assert found_by_email == user

    found_by_username = await finder.by_username(username)
    assert found_by_username == user
