from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.entities.refresh_token import RefreshToken
from app.domain.exceptions import AuthenticationError
from app.domain.repositories import RefreshTokenRepository, CacheRepository, UserRepository
from app.domain.services.token_service import TokenService


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str

class RefreshAccessToken:
    def __init__(
            self,
            token_service: TokenService,
            refresh_token_repository: RefreshTokenRepository,
            cache_repository: CacheRepository,
            user_repository: UserRepository):
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository
        self.cache_repository = cache_repository
        self.user_repository = user_repository

    async def execute(self, refresh_token: str) -> TokenPair:
        now = datetime.now(timezone.utc)

        payload = self.token_service.decode(refresh_token)
        if payload.token_type != "refresh":
            raise AuthenticationError("Invalid refresh token")

        if await self.cache_repository.get(f"blacklist:{payload.jti}") is not None:
            raise AuthenticationError("Invalid refresh token")

        storage = await self.refresh_token_repository.get_by_jti(payload.jti)
        if storage is None or not storage.is_active(now):
            raise AuthenticationError("Refresh token revoked or expired")

        user = await self.user_repository.get_by_id(storage.user_id)
        if user is None:
            raise AuthenticationError("Invalid refresh token")
        if not user.is_active:
            raise AuthenticationError("User is not active")
        if not user.is_verified:
            raise AuthenticationError("User is not verified")


        await self.refresh_token_repository.save(storage.revoke(now))
        await self.cache_repository.set(
            f"blacklist:{payload.jti}",
            str(user.id),
            payload.expires_at
        )

        access_token = self.token_service.create_access_token(user.id)
        refresh_token = self.token_service.create_refresh_token(user.id)

        await self.refresh_token_repository.create(
            RefreshToken.create(
                user_id=user.id,
                jti=refresh_token.jti,
                expires_at=refresh_token.expires_at,
                now = now,
            )
        )

        return TokenPair(access_token=access_token.token, refresh_token=refresh_token.token)