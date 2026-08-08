from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import config


class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
    pool_pre_ping=config.DB_POOL_PRE_PING,
    connect_args={
        "statement_cache_size": config.DB_STATEMENT_CACHE_SIZE
    },
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session per request or operation."""
    async with SessionLocal() as session:
        yield session