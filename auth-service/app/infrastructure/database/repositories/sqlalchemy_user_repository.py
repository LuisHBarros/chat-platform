from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.object_values import Email, Password, Username
from app.domain.entities.user import User
from app.infrastructure.database.models.user_model import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self.session.get(UserModel, user_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_email(self, email: Email) -> User | None   :
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_username(self, username: Username) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)


    async def save(self, user: User) -> User:
        model = await self.session.get(UserModel, user.id)
        if model is None:
            model = self._to_model(user)
            self.session.add(model)
        else:
            model.email = user.email.value
            model.username = user.username.value
            model.password_hash = user.password.hashed_value
            model.is_active = user.is_active
            model.is_verified = user.is_verified
            model.is_superuser = user.is_superuser
            model.updated_at = user.updated_at
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            username=Username(model.username),
            password=Password(model.password_hash),
            is_active=model.is_active,
            is_verified=model.is_verified,
            is_superuser=model.is_superuser,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email.value,
            username=user.username.value,
            password_hash=user.password.hashed_value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
