from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password
from app.domain.exceptions import AuthenticationError, UserNotActiveError, UserNotVerifiedError
from app.domain.services import AuthenticateUser
from test.domain.fake_repositories import (
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_authenticate_with_email_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    token_repo = FakeRefreshTokenRepository()
    token_service = FakeTokenService()

    email = Email("user@example.com")
    username = Username("user123")
    user = User.create(email, username, Password(hasher.hash("secret")), now).verify(now)
    await user_repo.save(user)

    auth_service = AuthenticateUser(user_repo, hasher, token_repo, token_service)
    result = await auth_service.with_email_and_password(email, "secret")

    assert result.user.id == user.id
    assert result.access_token is not None
    assert result.refresh_token is not None


@pytest.mark.asyncio
async def test_authenticate_with_username_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    token_repo = FakeRefreshTokenRepository()
    token_service = FakeTokenService()

    email = Email("user@example.com")
    username = Username("user123")
    user = User.create(email, username, Password(hasher.hash("secret")), now).verify(now)
    await user_repo.save(user)

    auth_service = AuthenticateUser(user_repo, hasher, token_repo, token_service)
    result = await auth_service.with_username_and_password(username, "secret")

    assert result.user.id == user.id


@pytest.mark.asyncio
async def test_authenticate_invalid_credentials():
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()
    token_repo = FakeRefreshTokenRepository()
    token_service = FakeTokenService()

    auth_service = AuthenticateUser(user_repo, hasher, token_repo, token_service)

    with pytest.raises(AuthenticationError):
        await auth_service.with_email_and_password(Email("nonexistent@example.com"), "secret")


@pytest.mark.asyncio
async def test_authenticate_unverified_user():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    email = Email("unverified@example.com")
    user = User.create(email, Username("unverified"), Password(hasher.hash("secret")), now)
    await user_repo.save(user)

    auth_service = AuthenticateUser(user_repo, hasher, FakeRefreshTokenRepository(), FakeTokenService())

    with pytest.raises(UserNotVerifiedError):
        await auth_service.with_email_and_password(email, "secret")


@pytest.mark.asyncio
async def test_authenticate_inactive_user():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    hasher = FakePasswordHasher()

    email = Email("inactive@example.com")
    user = User.create(email, Username("inactive"), Password(hasher.hash("secret")), now).verify(now).deactivate(now)
    await user_repo.save(user)

    auth_service = AuthenticateUser(user_repo, hasher, FakeRefreshTokenRepository(), FakeTokenService())

    with pytest.raises(UserNotActiveError):
        await auth_service.with_email_and_password(email, "secret")
