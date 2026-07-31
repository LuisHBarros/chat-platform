from app.domain.entities.object_values import Email, Username
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from uuid import UUID

class FindUser:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def by_id(self, user_id: UUID) -> User | None:
        return await self.user_repository.get_by_id(user_id)

    async def by_email(self, email: Email) -> User | None:
        return await self.user_repository.get_by_email(email)

    async def by_username(self, username: Username) -> User | None:
        return await self.user_repository.get_by_username(username)