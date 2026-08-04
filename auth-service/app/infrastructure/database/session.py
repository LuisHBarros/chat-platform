import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db"


def get_database_url() -> str:
    """Returns the database URL from environment variable or default fallback."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine(database_url: str | None = None, echo: bool = False) -> AsyncEngine:
    """Creates a new SQLAlchemy AsyncEngine instance."""
    url = database_url or get_database_url()
    return create_async_engine(
        url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: AsyncEngine | None = None,
    database_url: str | None = None,
    echo: bool = False,
) -> async_sessionmaker[AsyncSession]:
    """Creates an async_sessionmaker bound to an AsyncEngine."""
    db_engine = engine or create_engine(database_url=database_url, echo=echo)
    return async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# Module-level default engine and session factory
engine: AsyncEngine = create_engine()
AsyncSessionFactory: async_sessionmaker[AsyncSession] = create_session_factory(engine=engine)


from typing import Any

async def get_db_session(
    session_factory: Any = None,
) -> AsyncGenerator[AsyncSession]:
    """Async generator yielding an AsyncSession for database operations.

    Commits the transaction on success, rolls back on exception, and ensures closure.
    Can be used as a FastAPI dependency or async context generator.
    """
    factory = session_factory or AsyncSessionFactory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


get_session = get_db_session

__all__ = [
    "DEFAULT_DATABASE_URL",
    "AsyncSessionFactory",
    "create_engine",
    "create_session_factory",
    "engine",
    "get_database_url",
    "get_db_session",
    "get_session",
]
