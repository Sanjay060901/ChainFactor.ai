"""Database engine and session configuration.

Supports both PostgreSQL (production) and SQLite (local dev without Docker).
"""

import logging
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.get_database_url()

# SQLite needs special handling
_is_sqlite = db_url.startswith("sqlite")

engine_kwargs: dict = {
    "echo": settings.DEBUG,
    "pool_pre_ping": not _is_sqlite,  # pool_pre_ping not supported by SQLite
}

if not _is_sqlite:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(db_url, **engine_kwargs)

# Enable SQLite foreign keys and WAL mode for better concurrency
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
    logger.info("Using SQLite database (local dev mode)")

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
