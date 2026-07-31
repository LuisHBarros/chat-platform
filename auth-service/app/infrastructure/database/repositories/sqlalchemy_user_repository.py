from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.database.models.user_model import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User:
        model = await self.session.get(UserModel, user_id)
        if model is None:
            raise LookupError("User not found")
        return self._to_domain(model)

    async def get_by_email(self, email: str) -> User:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise LookupError("User not found")
        return self._to_domain(model)

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def change_password(self, user_id: UUID, password_hash: str) -> User:
        model = await self.session.get(UserModel, user_id)
        if model is None:
            raise LookupError("User not found")

        model.password_hash = password_hash
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, user_id: UUID) -> None:
        model = await self.session.get(UserModel, user_id)
        if model is None:
            raise LookupError("User not found")

        model.is_active = False
        await self.session.flush()

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,
            is_active=model.is_active,
            is_verified=model.is_verified,
            is_superuser=model.is_superuser,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
