from datetime import datetime, timezone
from uuid import uuid4
import pytest

from app.domain.entities import TokenPayload, RefreshToken
from app.domain.exceptions import ValidationError
from app.domain.services import LogoutUser
from test.domain.fake_repositories import FakeCacheRepository, FakeRefreshTokenRepository


@pytest.mark.asyncio
async def test_logout_user_blacklists_cache_and_revokes_db():
    cache_repo = FakeCacheRepository()
    token_repo = FakeRefreshTokenRepository()
    logout_service = LogoutUser(cache_repo, token_repo)

    now = datetime.now(timezone.utc)
    user_id = uuid4()
    jti = uuid4()

    # Pre-populate token in DB repository
    db_token = RefreshToken.create(user_id, jti, now, now)
    await token_repo.create(db_token)

    payload = TokenPayload(
        user_id=user_id,
        jti=jti,
        expires_at=now,
        token_type="refresh",
    )

    await logout_service.execute(payload)

    # Check cache blacklist
    blacklisted = await cache_repo.get(f"blacklist:{jti}")
    assert blacklisted == str(user_id)

    # Check DB revocation
    revoked_token = await token_repo.get_by_jti(jti)
    assert revoked_token is not None
    assert revoked_token.revoked_at is not None


@pytest.mark.asyncio
async def test_logout_user_no_payloads_raises_error():
    cache_repo = FakeCacheRepository()
    logout_service = LogoutUser(cache_repo)

    with pytest.raises(ValidationError, match="No token payloads provided"):
        await logout_service.execute()
