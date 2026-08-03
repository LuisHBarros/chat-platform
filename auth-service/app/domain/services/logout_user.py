import asyncio

from app.domain.entities.token_payload import TokenPayload
from app.domain.exceptions import ValidationError
from app.domain.repositories.cache_repository import CacheRepository
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository


class LogoutUser:
    def __init__(
        self,
        cache_repository: CacheRepository,
        refresh_token_repository: RefreshTokenRepository | None = None,
    ):
        self.cache_repository = cache_repository
        self.refresh_token_repository = refresh_token_repository

    async def execute(self, *token_payloads: TokenPayload) -> None:
        if not token_payloads:
            raise ValidationError("No token payloads provided")

        tasks = []
        for token_payload in token_payloads:
            tasks.append(
                self.cache_repository.set(
                    f"blacklist:{token_payload.jti}",
                    str(token_payload.user_id),
                    token_payload.expires_at,
                )
            )

            if self.refresh_token_repository is not None and token_payload.token_type == "refresh":
                tasks.append(self.refresh_token_repository.revoke(token_payload.jti))

        await asyncio.gather(*tasks)
