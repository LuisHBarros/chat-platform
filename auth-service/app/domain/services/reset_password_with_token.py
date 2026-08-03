from datetime import UTC, datetime

from app.domain.entities.object_values import Password
from app.domain.entities.user import User
from app.domain.exceptions import DomainError, ValidationError
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.verification_token_repository import VerificationTokenRepository
from app.domain.services.password_hasher import PasswordHasher


class InvalidTokenError(DomainError):
    """Raised when token is invalid, expired, or already used."""


class ResetPasswordWithToken:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: VerificationTokenRepository,
        password_hasher: PasswordHasher,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.password_hasher = password_hasher

    async def execute(self, token_str: str, new_password: str) -> User:
        if not token_str:
            raise ValidationError("Token is required")

        if not new_password:
            raise ValidationError("New password is required")

        now = datetime.now(UTC)

        # 1. Look up token in repository
        token = await self.token_repository.get_by_token(token_str, "password_reset")
        if token is None or not token.is_valid(now):
            raise InvalidTokenError("Invalid or expired password reset token")

        # 2. Retrieve target user
        user = await self.user_repository.get_by_id(token.user_id)
        if user is None:
            raise InvalidTokenError("User associated with token was not found")

        # 3. Apply domain transformations
        hashed_password = self.password_hasher.hash(new_password)
        updated_user = user.change_password(Password(hashed_password), now)
        used_token = token.mark_as_used(now)

        # 4. Persist changes
        await self.token_repository.save(used_token)
        return await self.user_repository.save(updated_user)
