from datetime import datetime, timezone
import pytest

from app.domain.entities import User, Email, Username, Password, RefreshToken
from app.domain.exceptions import AuthenticationError, ValidationError
from app.domain.services import RotateRefreshToken
from test.domain.fake_repositories import (
    FakeCacheRepository,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_rotate_refresh_token_success():
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

    rotator = RotateRefreshToken(cache_repo, token_repo, token_service, user_repo)
    result = await rotator.execute(issued_refresh.token)

    assert result.access_token is not None
    assert result.refresh_token is not None

    # Check old token is revoked
    old_token = await token_repo.get_by_jti(issued_refresh.jti)
    assert old_token.revoked_at is not None


@pytest.mark.asyncio
async def test_rotate_refresh_token_blacklisted():
    now = datetime.now(timezone.utc)
    user_repo = FakeUserRepository()
    token_repo = FakeRefreshTokenRepository()
    cache_repo = FakeCacheRepository()
    token_service = FakeTokenService()

    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now).verify(now)
    await user_repo.save(user)

    issued_refresh = token_service.create_refresh_token(user.id)
    await cache_repo.set(f"blacklist:{issued_refresh.jti}", str(user.id), now)

    rotator = RotateRefreshToken(cache_repo, token_repo, token_service, user_repo)

    with pytest.raises(AuthenticationError, match="Token has been revoked"):
        await rotator.execute(issued_refresh.token)
