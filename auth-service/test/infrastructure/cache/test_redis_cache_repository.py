from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.domain.repositories.cache_repository import CacheRepository
from app.infrastructure.cache.redis_cache_repository import RedisCacheRepository


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    return mock


def test_redis_cache_repository_implements_protocol(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    assert isinstance(repo, CacheRepository)


@pytest.mark.asyncio
async def test_set_key_with_future_expiration(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    expires_at = datetime.now(UTC) + timedelta(minutes=15)

    await repo.set("blacklist:jti-123", "user-456", expires_at)

    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args == ("blacklist:jti-123", "user-456")
    assert "ex" in kwargs
    assert kwargs["ex"] > 0 and kwargs["ex"] <= 900


@pytest.mark.asyncio
async def test_set_key_with_naive_datetime(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    naive_expires_at = datetime.now() + timedelta(minutes=10)

    await repo.set("blacklist:jti-naive", "user-789", naive_expires_at)

    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args == ("blacklist:jti-naive", "user-789")
    assert "ex" in kwargs
    assert kwargs["ex"] > 0 and kwargs["ex"] <= 600


@pytest.mark.asyncio
async def test_set_key_with_past_expiration(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    past_expires_at = datetime.now(UTC) - timedelta(minutes=5)

    await repo.set("blacklist:expired", "user-111", past_expires_at)

    mock_redis.set.assert_called_once_with("blacklist:expired", "user-111", ex=1)


@pytest.mark.asyncio
async def test_get_key_none(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    mock_redis.get.return_value = None

    result = await repo.get("nonexistent_key")

    assert result is None
    mock_redis.get.assert_called_once_with("nonexistent_key")


@pytest.mark.asyncio
async def test_get_key_bytes(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    mock_redis.get.return_value = b"some_value"

    result = await repo.get("key_with_bytes")

    assert result == "some_value"
    mock_redis.get.assert_called_once_with("key_with_bytes")


@pytest.mark.asyncio
async def test_get_key_str(mock_redis):
    repo = RedisCacheRepository(mock_redis)
    mock_redis.get.return_value = "str_value"

    result = await repo.get("key_with_str")

    assert result == "str_value"
    mock_redis.get.assert_called_once_with("key_with_str")


@pytest.mark.asyncio
async def test_delete_key(mock_redis):
    repo = RedisCacheRepository(mock_redis)

    await repo.delete("blacklist:jti-to-del")

    mock_redis.delete.assert_called_once_with("blacklist:jti-to-del")


@pytest.mark.asyncio
async def test_publish_event(mock_redis):
    repo = RedisCacheRepository(mock_redis)

    await repo.publish("auth_events", '{"event": "logout", "user_id": "123"}')

    mock_redis.publish.assert_called_once_with("auth_events", '{"event": "logout", "user_id": "123"}')
