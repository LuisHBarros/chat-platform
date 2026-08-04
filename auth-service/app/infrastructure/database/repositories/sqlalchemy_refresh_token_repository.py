from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories import RefreshTokenRepository
from app.infrastructure.database.models.refresh_token_model import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_jti(self, jti: UUID) -> RefreshToken | None:
        result = await self.session.execute(select(RefreshTokenModel).where(RefreshTokenModel.jti == jti))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def create(self, refresh_token: RefreshToken) -> None:
        model = self._to_model(refresh_token)
        self.session.add(model)
        await self.session.flush()

    async def save(self, refresh_token: RefreshToken) -> None:
        model = await self.session.get(RefreshTokenModel, refresh_token.id)
        if model is None:
            model = self._to_model(refresh_token)
            self.session.add(model)
        else:
            model.expires_at = refresh_token.expires_at
            model.revoked_at = refresh_token.revoked_at
        await self.session.flush()

    async def revoke(self, jti: UUID) -> None:
        result = await self.session.execute(select(RefreshTokenModel).where(RefreshTokenModel.jti == jti))
        model = result.scalar_one_or_none()
        if model is not None:
            model.revoked_at = datetime.now(UTC)
            await self.session.flush()

    def _to_domain(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            jti=model.jti,
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
        )

    def _to_model(self, refresh_token: RefreshToken) -> RefreshTokenModel:
        return RefreshTokenModel(
            id=refresh_token.id,
            user_id=refresh_token.user_id,
            jti=refresh_token.jti,
            expires_at=refresh_token.expires_at,
            created_at=refresh_token.created_at,
            revoked_at=refresh_token.revoked_at,
        )
