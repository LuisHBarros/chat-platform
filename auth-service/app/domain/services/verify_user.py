from datetime import UTC, datetime

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


class VerifyUser:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user: User) -> User:
        now = datetime.now(UTC)
        user = user.verify(now)
        return await self.user_repository.save(user)
