from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.entities.object_values import Email, Username
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.token_payload import IssuedToken, TokenPayload
from app.domain.entities.token_payload import TokenType as JWTTokenType
from app.domain.entities.user import User
from app.domain.entities.verification_token import TokenType as VerificationTokenType
from app.domain.entities.verification_token import VerificationToken
from app.domain.repositories import (
    CacheRepository,
    RefreshTokenRepository,
    UserRepository,
    VerificationTokenRepository,
)
from app.domain.services.password_hasher import PasswordHasher
from app.domain.services.token_service import TokenService


class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_username(self, username: Username) -> User | None:
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self):
        self.tokens: dict[UUID, RefreshToken] = {}

    async def get_by_jti(self, jti: UUID) -> RefreshToken | None:
        for token in self.tokens.values():
            if token.jti == jti:
                return token
        return None

    async def create(self, refresh_token: RefreshToken) -> None:
        self.tokens[refresh_token.id] = refresh_token

    async def save(self, refresh_token: RefreshToken) -> None:
        self.tokens[refresh_token.id] = refresh_token

    async def revoke(self, jti: UUID) -> None:
        token = await self.get_by_jti(jti)
        if token:
            now = datetime.now(UTC)
            self.tokens[token.id] = token.revoke(now)


class FakeCacheRepository(CacheRepository):
    def __init__(self):
        self.storage: dict[str, str] = {}

    async def set(self, key: str, value: str, expires_at: datetime) -> None:
        self.storage[key] = value

    async def get(self, key: str) -> str | None:
        return self.storage.get(key)

    async def delete(self, key: str) -> None:
        self.storage.pop(key, None)

    async def publish(self, key: str, value: str) -> None:
        self.storage[key] = value


class FakeVerificationTokenRepository(VerificationTokenRepository):
    def __init__(self):
        self.tokens: dict[UUID, VerificationToken] = {}

    async def create(self, token: VerificationToken) -> None:
        self.tokens[token.id] = token

    async def get_by_token(self, token: str, token_type: VerificationTokenType) -> VerificationToken | None:
        for item in self.tokens.values():
            if item.token == token and item.token_type == token_type:
                return item
        return None

    async def save(self, token: VerificationToken) -> None:
        self.tokens[token.id] = token


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed_{password}"


class FakeTokenService(TokenService):
    def create_access_token(self, user_id: UUID) -> IssuedToken:
        jti = uuid4()
        now = datetime.now(UTC)
        return IssuedToken(
            token=f"access_token_{user_id}_{jti}",
            jti=jti,
            expires_at=now + timedelta(minutes=15),
            token_type="access",
        )

    def create_refresh_token(self, user_id: UUID) -> IssuedToken:
        jti = uuid4()
        now = datetime.now(UTC)
        return IssuedToken(
            token=f"refresh_token_{user_id}_{jti}",
            jti=jti,
            expires_at=now + timedelta(days=7),
            token_type="refresh",
        )

    def decode(self, token: str) -> TokenPayload:
        parts = token.split("_")
        user_id = UUID(parts[2])
        jti = UUID(parts[3])
        raw_type = parts[0]
        token_type: JWTTokenType = "refresh" if raw_type == "refresh" else "access"
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=7) if token_type == "refresh" else now + timedelta(minutes=15)
        return TokenPayload(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            token_type=token_type,
        )
