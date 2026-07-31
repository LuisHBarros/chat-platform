from dataclasses import asdict
from app.domain.repositories.cache_repository import CacheRepository
from app.domain.entities.logout_payload import LogoutPayload
from uuid import UUID
from datetime import datetime, timezone
import json
from datetime import timedelta
import os

class LogoutUser:

    def __init__(self, cache_repository: CacheRepository):
        self.cache_repository = cache_repository

    async def execute(self, user_id: UUID) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_IN_SECONDS")))

        payload = LogoutPayload(
            user_id=user_id,
            token_type="access",
            expires_at=expires_at,
        )

        payload_json = json.dumps({
            "user_id": str(payload.user_id),
            "token_type": payload.token_type,
            "expires_at": payload.expires_at.isoformat(),
        })

        await self.cache_repository.set(f"token:{user_id}", payload_json, expires_at)
        return None