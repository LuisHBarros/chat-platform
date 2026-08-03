from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password, RefreshToken
from app.domain.exceptions import AuthenticationError
from app.domain.services import RefreshAccessToken
from test.domain.fake_repositories import (
    FakeCacheRepository,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_refresh_access_token_success():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    token_repo = FakeRefreshTokenRepository()
    cache_repo = FakeCacheRepository()
    token_service = FakeTokenService()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now).verify(now)
    await user_repo.save(user)

    issued_refresh = token_service.create_refresh_token(user.id)
    db_token = RefreshToken.create(user.id, issued_refresh.jti, issued_refresh.expires_at, now)
    await token_repo.create(db_token)

    refresher = RefreshAccessToken(token_service, token_repo, cache_repo, user_repo)
    result = await refresher.execute(issued_refresh.token)

    assert result.access_token is not None
    assert result.refresh_token is not None


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token_type():
    token_service = FakeTokenService()
    user_repo = FakeUserRepository()
    token_repo = FakeRefreshTokenRepository()
    cache_repo = FakeCacheRepository()

    refresher = RefreshAccessToken(token_service, token_repo, cache_repo, user_repo)

    access_token = token_service.create_access_token(User.create(Email("a@b.com"), Username("aaa"), Password("p"), datetime.now(timezone.utc)).id).token

    with pytest.raises(AuthenticationError, match="Invalid refresh token"):
        await refresher.execute(access_token)
