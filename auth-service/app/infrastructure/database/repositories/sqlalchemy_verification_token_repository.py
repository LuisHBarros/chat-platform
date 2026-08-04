from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.verification_token import TokenType, VerificationToken
from app.domain.repositories import VerificationTokenRepository
from app.infrastructure.database.models.verification_token_model import VerificationTokenModel


class SqlAlchemyVerificationTokenRepository(VerificationTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: VerificationToken) -> None:
        model = self._to_model(token)
        self.session.add(model)
        await self.session.flush()

    async def get_by_token(self, token: str, token_type: TokenType) -> VerificationToken | None:
        result = await self.session.execute(
            select(VerificationTokenModel).where(
                VerificationTokenModel.token == token,
                VerificationTokenModel.token_type == token_type,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def save(self, token: VerificationToken) -> None:
        model = await self.session.get(VerificationTokenModel, token.id)
        if model is None:
            model = self._to_model(token)
            self.session.add(model)
        else:
            model.expires_at = token.expires_at
            model.used_at = token.used_at
        await self.session.flush()

    def _to_domain(self, model: VerificationTokenModel) -> VerificationToken:
        return VerificationToken(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            token_type=model.token_type,  # type: ignore[arg-type]
            expires_at=model.expires_at,
            created_at=model.created_at,
            used_at=model.used_at,
        )

    def _to_model(self, token: VerificationToken) -> VerificationTokenModel:
        return VerificationTokenModel(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            token_type=token.token_type,
            expires_at=token.expires_at,
            created_at=token.created_at,
            used_at=token.used_at,
        )
