import asyncio
from app.domain.exceptions import ValidationError
from app.domain.repositories.cache_repository import CacheRepository
from app.domain.entities.token_payload import TokenPayload

class LogoutUser:

    def __init__(self, cache_repository: CacheRepository):
        self.cache_repository = cache_repository

    async def execute(self, *token_payloads: TokenPayload) -> None:

        if not token_payloads:
            raise ValidationError   ("No token payloads provided")

        await asyncio.gather(*[
            self.cache_repository.set(
                f"blacklist:{token_payload.jti}",
                str(token_payload.user_id),
                token_payload.expires_at,
            )
            for token_payload in token_payloads
        ])
