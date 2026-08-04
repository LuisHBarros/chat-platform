from datetime import UTC, datetime

from redis.asyncio import Redis

from app.domain.repositories.cache_repository import CacheRepository


class RedisCacheRepository(CacheRepository):
    """Concrete implementation of CacheRepository using Redis async client (redis.asyncio)."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def set(self, key: str, value: str, expires_at: datetime) -> None:
        """Sets key-value pair in Redis with expiration datetime.

        Used for real-time JWT token blacklisting during logout, key expiration, etc.
        """
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        ttl = int((expires_at - now).total_seconds())

        if ttl > 0:
            await self.redis.set(key, value, ex=ttl)
        else:
            # If expiration datetime is in the past, set short expiration
            await self.redis.set(key, value, ex=1)

    async def get(self, key: str) -> str | None:
        """Retrieves string value for the specified key from Redis."""
        result = await self.redis.get(key)
        if result is None:
            return None
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return str(result)

    async def delete(self, key: str) -> None:
        """Deletes key from Redis."""
        await self.redis.delete(key)

    async def publish(self, key: str, value: str) -> None:
        """Publishes value to a pub/sub channel identified by key."""
        await self.redis.publish(key, value)
