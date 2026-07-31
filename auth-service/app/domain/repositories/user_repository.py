from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(Protocol):

    async def get_by_id(self, user_id: UUID) -> User:
        ...

    async def get_by_email(self, email: str) -> User:
        ...

    async def save(self, user: User) -> User:
        ...

    async def change_password(self, user_id: UUID, password_hash: str) -> User:
        ...

    async def delete(self, user_id: UUID) -> None:
        ...

