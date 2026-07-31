from app.domain.entities.object_values import Email, Username
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher

class AuthenticateUser:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def with_email_and_password(self, email: Email, password: str) -> User | None:
        user = await self.user_repository.get_by_email(email)
        if user is None or not self.password_hasher.verify(password, user.password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User is not active")
        
        if not user.is_verified:
            raise ValueError("User is not verified")

        return user

    async def with_username_and_password(self, username: Username, password: str) -> User | None:
        user = await self.user_repository.get_by_username(username)
        if user is None or not self.password_hasher.verify(password, user.password):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError("User is not active")

        if not user.is_verified:
            raise ValueError("User is not verified")

        return user
