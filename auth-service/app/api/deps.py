import os

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import CacheRepository
from app.domain.services import PasswordHasher, TokenService
from app.infrastructure.cache.redis_cache_repository import RedisCacheRepository
from app.infrastructure.database.repositories import (
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyVerificationTokenRepository,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.email.smtp_email_adapter import SMTPEmailAdapter
from app.infrastructure.security.bcrypt_hasher import BcryptHasher
from app.infrastructure.security.jwt_token_service import JwtTokenService

_password_hasher = BcryptHasher()
_email_adapter = SMTPEmailAdapter()

def get_password_hasher() -> PasswordHasher:
    return _password_hasher

def get_token_service() -> TokenService:
    secret_key = os.getenv("SECRET_KEY", "super-secret-dev-key-change-in-prod")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    return JwtTokenService(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=access_minutes,
        refresh_token_expire_days=refresh_days,
    )

def get_email_adapter() -> SMTPEmailAdapter:
    return _email_adapter

async def get_cache_repository() -> CacheRepository | None:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        from redis.asyncio import Redis
        redis_client = Redis.from_url(redis_url, socket_timeout=3.0)
        return RedisCacheRepository(redis_client)
    except Exception:
        return None

def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)

def get_refresh_token_repository(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyRefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)

def get_verification_token_repository(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyVerificationTokenRepository:
    return SqlAlchemyVerificationTokenRepository(session)
