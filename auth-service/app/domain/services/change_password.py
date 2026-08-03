from datetime import UTC, datetime

from app.domain.entities.object_values import Password
from app.domain.entities.user import User
from app.domain.exceptions import ValidationError
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher


class ChangePassword:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def execute(self, user: User, new_password: str) -> User:
        if not new_password:
            raise ValidationError("New password is required")
        now = datetime.now(UTC)
        hashed = self.password_hasher.hash(new_password)
        user = user.change_password(Password(hashed), now)
        return await self.user_repository.save(user)
