from typing import Protocol
from uuid import UUID

from app.domain.entities.object_values import Email, Username
from app.domain.entities.user import User


class UserRepository(Protocol):

    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    async def get_by_email(self, email: Email) -> User | None:
        ...

    async def get_by_username(self, username: Username) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...

