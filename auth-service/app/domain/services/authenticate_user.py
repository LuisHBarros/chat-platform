from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.entities.object_values import Email, Username
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.exceptions import AuthenticationError, UserNotActiveError, UserNotVerifiedError
from app.domain.repositories import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService


@dataclass(frozen=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


class AuthenticateUser:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.refresh_token_repository = refresh_token_repository
        self.token_service = token_service

    async def with_email_and_password(self, email: Email, password: str) -> AuthResult:
        user = await self.user_repository.get_by_email(email)
        self._verify_credentials(user, password, "Invalid email or password")
        assert user is not None
        self._ensure_user_can_authenticate(user)
        return await self._issue_tokens(user)

    async def with_username_and_password(self, username: Username, password: str) -> AuthResult:
        user = await self.user_repository.get_by_username(username)
        self._verify_credentials(user, password, "Invalid username or password")
        assert user is not None
        self._ensure_user_can_authenticate(user)
        return await self._issue_tokens(user)

    def _verify_credentials(self, user: User | None, password: str, error_message: str) -> None:
        if user is None or not self.password_hasher.verify(password, user.password.hashed_value):
            raise AuthenticationError(error_message)

    def _ensure_user_can_authenticate(self, user: User) -> None:
        if not user.is_active:
            raise UserNotActiveError("User is not active")

        if not user.is_verified:
            raise UserNotVerifiedError("User is not verified")

    async def _issue_tokens(self, user: User) -> AuthResult:
        now = datetime.now(UTC)

        access = self.token_service.create_access_token(user.id)
        refresh = self.token_service.create_refresh_token(user.id)

        entity = RefreshToken.create(
            user_id=user.id,
            jti=refresh.jti,
            expires_at=refresh.expires_at,
            now=now,
        )
        await self.refresh_token_repository.create(entity)

        return AuthResult(user=user, access_token=access.token, refresh_token=refresh.token)
