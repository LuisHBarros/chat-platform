import os

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.session import (
    DEFAULT_DATABASE_URL,
    create_engine,
    create_session_factory,
    get_database_url,
    get_db_session,
    get_session,
)


def test_get_database_url_default():
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    assert get_database_url() == DEFAULT_DATABASE_URL


def test_get_database_url_override(monkeypatch):
    custom_url = "postgresql+asyncpg://user:pass@localhost:5432/custom_db"
    monkeypatch.setenv("DATABASE_URL", custom_url)
    assert get_database_url() == custom_url


def test_create_engine():
    test_engine = create_engine("sqlite+aiosqlite:///:memory:")
    assert isinstance(test_engine, AsyncEngine)


def test_create_session_factory():
    test_engine = create_engine("sqlite+aiosqlite:///:memory:")
    factory = create_session_factory(engine=test_engine)
    assert isinstance(factory, async_sessionmaker)


@pytest.mark.asyncio
async def test_get_db_session_success():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    session_gen = get_db_session(session_factory=factory)
    session = await anext(session_gen)
    assert isinstance(session, AsyncSession)
    assert session.is_active

    # Finish the generator cleanly (success path -> commit)
    with pytest.raises(StopAsyncIteration):
        await anext(session_gen)

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_rollback_on_exception():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    session_gen = get_db_session(session_factory=factory)
    session = await anext(session_gen)
    assert isinstance(session, AsyncSession)

    # Throw an exception into the generator to trigger rollback & exception re-raise
    with pytest.raises(RuntimeError, match="Database error occurred"):
        await session_gen.athrow(RuntimeError("Database error occurred"))

    await engine.dispose()


def test_get_session_alias():
    assert get_session is get_db_session
