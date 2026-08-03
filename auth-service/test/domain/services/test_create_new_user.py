import pytest

from app.domain.entities.object_values import Email, Username
from app.domain.exceptions import UserAlreadyExistsError, ValidationError
from app.domain.services import CreateNewUser
from test.domain.fake_repositories import FakePasswordHasher, FakeUserRepository


@pytest.mark.asyncio
async def test_create_new_user_success():
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    service = CreateNewUser(user_repo, hasher)

    email = Email("newuser@example.com")
    username = Username("newuser")

    user = await service.execute(email, username, "secret123")

    assert user.id is not None
    assert user.email == email
    assert user.username == username
    assert user.password.hashed_value == "hashed_secret123"
    assert await user_repo.get_by_id(user.id) == user


@pytest.mark.asyncio
async def test_create_new_user_duplicate_email():
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    service = CreateNewUser(user_repo, hasher)

    email = Email("user@example.com")

    await service.execute(email, Username("user1"), "pass123")

    with pytest.raises(UserAlreadyExistsError, match="email already exists"):
        await service.execute(email, Username("user2"), "pass123")


@pytest.mark.asyncio
async def test_create_new_user_duplicate_username():
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    service = CreateNewUser(user_repo, hasher)

    username = Username("uniqueuser")

    await service.execute(Email("u1@example.com"), username, "pass123")

    with pytest.raises(UserAlreadyExistsError, match="username already exists"):
        await service.execute(Email("u2@example.com"), username, "pass123")


@pytest.mark.asyncio
async def test_create_new_user_empty_password():
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    service = CreateNewUser(user_repo, hasher)

    with pytest.raises(ValidationError, match="Password is required"):
        await service.execute(Email("user@example.com"), Username("user123"), "")
