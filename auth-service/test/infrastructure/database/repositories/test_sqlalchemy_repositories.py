from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.object_values import Email, Password, Username
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.entities.verification_token import VerificationToken
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.repositories import (
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyVerificationTokenRepository,
)


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_repository(async_session: AsyncSession):
    repo = SqlAlchemyUserRepository(async_session)
    now = datetime.now(UTC)

    user = User.create(
        email=Email("test@example.com"),
        username=Username("testuser"),
        password=Password("$2b$12$eImiTXuWVxfM37uY4JANjO5E/80u34m2m335gK1e12e12e12e12e1"),
        now=now,
    )

    # Save
    saved_user = await repo.save(user)
    assert saved_user.id == user.id
    assert saved_user.email.value == "test@example.com"

    # Get by ID
    by_id = await repo.get_by_id(user.id)
    assert by_id is not None
    assert by_id.username.value == "testuser"

    # Get by email
    by_email = await repo.get_by_email(Email("test@example.com"))
    assert by_email is not None
    assert by_email.id == user.id

    # Get by username
    by_username = await repo.get_by_username(Username("testuser"))
    assert by_username is not None
    assert by_username.id == user.id


@pytest.mark.asyncio
async def test_refresh_token_repository(async_session: AsyncSession):
    user_repo = SqlAlchemyUserRepository(async_session)
    token_repo = SqlAlchemyRefreshTokenRepository(async_session)
    now = datetime.now(UTC)

    # First create user for FK constraint
    user = User.create(
        email=Email("refresh@example.com"),
        username=Username("refreshuser"),
        password=Password("$2b$12$eImiTXuWVxfM37uY4JANjO5E/80u34m2m335gK1e12e12e12e12e1"),
        now=now,
    )
    await user_repo.save(user)

    jti = uuid4()
    refresh_token = RefreshToken.create(
        user_id=user.id,
        jti=jti,
        expires_at=now,
        now=now,
    )

    # Create
    await token_repo.create(refresh_token)

    # Get by JTI
    fetched = await token_repo.get_by_jti(jti)
    assert fetched is not None
    assert fetched.jti == jti
    assert fetched.user_id == user.id
    assert fetched.revoked_at is None

    # Revoke
    await token_repo.revoke(jti)
    revoked = await token_repo.get_by_jti(jti)
    assert revoked is not None
    assert revoked.revoked_at is not None


@pytest.mark.asyncio
async def test_verification_token_repository(async_session: AsyncSession):
    user_repo = SqlAlchemyUserRepository(async_session)
    token_repo = SqlAlchemyVerificationTokenRepository(async_session)
    now = datetime.now(UTC)

    # Create user for FK constraint
    user = User.create(
        email=Email("verify@example.com"),
        username=Username("verifyuser"),
        password=Password("$2b$12$eImiTXuWVxfM37uY4JANjO5E/80u34m2m335gK1e12e12e12e12e1"),
        now=now,
    )
    await user_repo.save(user)

    verification_token, raw_str = VerificationToken.create(
        user_id=user.id,
        token_type="email_verification",
        now=now,
    )

    # Create
    await token_repo.create(verification_token)

    # Get by token
    fetched = await token_repo.get_by_token(raw_str, "email_verification")
    assert fetched is not None
    assert fetched.token == raw_str
    assert fetched.used_at is None

    # Save / Update (mark used)
    updated = fetched.mark_as_used(now)
    await token_repo.save(updated)

    after_save = await token_repo.get_by_token(raw_str, "email_verification")
    assert after_save is not None
    assert after_save.used_at is not None
