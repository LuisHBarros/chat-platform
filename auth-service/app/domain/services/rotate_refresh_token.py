from datetime import UTC, datetime

from app.domain.entities import RefreshToken
from app.domain.exceptions import AuthenticationError, ValidationError
from app.domain.repositories import CacheRepository, RefreshTokenRepository, UserRepository
from app.domain.services.authenticate_user import AuthResult
from app.domain.services.token_service import TokenService


class RotateRefreshToken:
    def __init__(
        self,
        cache_repository: CacheRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        user_repository: UserRepository,
    ):
        self.cache_repository = cache_repository
        self.refresh_token_repository = refresh_token_repository
        self.token_service = token_service
        self.user_repository = user_repository

    async def execute(self, refresh_token_str: str):
        if not refresh_token_str:
            raise ValidationError("Refresh token is required")

        now = datetime.now(UTC)

        payload = self.token_service.decode(refresh_token_str)
        if payload.token_type != "refresh":
            raise ValidationError("Provided token is not a refresh token")

        if self.cache_repository is not None:
            is_blacklisted = await self.cache_repository.get(f"blacklist:{payload.jti}")
            if is_blacklisted:
                raise AuthenticationError("Token has been revoked")

        token_entity = await self.refresh_token_repository.get_by_jti(payload.jti)
        if token_entity is None or not token_entity.is_active(now):
            raise AuthenticationError("Refresh token is invalid, expired or revoked")

        user = await self.user_repository.get_by_id(payload.user_id)
        if user is None or not user.can_authenticate():
            raise AuthenticationError("User is no longer active or verified")

        revoked_entity = token_entity.revoke(now)
        await self.refresh_token_repository.save(revoked_entity)
        new_refresh_token = self.token_service.create_refresh_token(user.id)
        new_access_token = self.token_service.create_access_token(user.id)

        new_token_entity = RefreshToken.create(
            user_id=user.id, jti=new_refresh_token.jti, expires_at=new_refresh_token.expires_at, now=now
        )
        await self.refresh_token_repository.create(new_token_entity)

        return AuthResult(
            user=user,
            access_token=new_access_token.token,
            refresh_token=new_refresh_token.token,
        )
