"""Shared pytest fixtures for the ChainFactor AI test suite."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base
from app.models.user import User

# Force DEMO_MODE for tests
settings.DEMO_MODE = True

# In-memory SQLite for tests (async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

# --- SQLite compatibility: map PostgreSQL types to SQLite equivalents ---
# JSONB -> JSON, UUID -> String(36)
_pg_to_sqlite = {JSONB: JSON, UUID: lambda: JSON()}


@event.listens_for(Base.metadata, "column_reflect")
def _reflect_col(inspector, table, column_info):
    pass  # Not needed for create_all, but keeps the hook registered


# Monkey-patch JSONB to compile as JSON on SQLite
from sqlalchemy.dialects.sqlite import base as sqlite_base  # noqa: E402

_original_visit = getattr(sqlite_base.SQLiteTypeCompiler, "visit_JSON", None)

if not hasattr(sqlite_base.SQLiteTypeCompiler, "visit_JSONB"):
    sqlite_base.SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

if not hasattr(sqlite_base.SQLiteTypeCompiler, "visit_UUID"):
    sqlite_base.SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "TEXT"


# --- Monkey-patch Uuid base type to serialize/deserialize as text on SQLite ---
# The Uuid.result_processor creates a processor that calls uuid.UUID(value), but
# SQLite stores UUID hex strings as floats due to numeric affinity. We override
# the bind_processor to store UUIDs as dash-prefixed strings (non-numeric), and
# the result_processor to handle both float and string values.
from sqlalchemy.sql.sqltypes import Uuid as _SqlaUuid  # noqa: E402

_original_uuid_bind_processor = _SqlaUuid.bind_processor
_original_uuid_result_processor = _SqlaUuid.result_processor


def _uuid_bind_processor(self, dialect):
    """Return a bind processor that converts uuid.UUID to string for any dialect."""
    if getattr(dialect, "supports_native_uuid", False):
        return _original_uuid_bind_processor(self, dialect)

    # Non-native UUID dialects (SQLite): always convert to string
    if self.as_uuid:

        def process(value):
            if value is not None:
                if isinstance(value, uuid.UUID):
                    return str(value)
                return value
            return value

        return process

    return None


def _uuid_result_processor(self, dialect, coltype):
    """Return a result processor that handles float/string -> uuid.UUID for SQLite."""
    if getattr(dialect, "supports_native_uuid", False):
        return _original_uuid_result_processor(self, dialect, coltype)

    # Non-native UUID dialects (SQLite)
    if self.as_uuid:

        def process(value):
            if value is None:
                return value
            if isinstance(value, uuid.UUID):
                return value
            if isinstance(value, (int, float)):
                # SQLite stored the hex as a numeric; convert back via int
                return uuid.UUID(int=int(value))
            return uuid.UUID(str(value))

        return process

    return None


_SqlaUuid.bind_processor = _uuid_bind_processor
_SqlaUuid.result_processor = _uuid_result_processor


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    """Create async engine for test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Provide a transactional database session that rolls back after each test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create or retrieve the test user in the database.

    Uses merge() instead of add() so this fixture is idempotent across tests that
    call await db.commit() (e.g. endpoint tests that update NFT status).  Those
    commits permanently write the row to the session-scoped SQLite engine; a
    subsequent add() would raise UNIQUE constraint errors when the next test
    tries to create the same user.
    """
    user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        cognito_sub="test-cognito-sub-001",
        name="Test User",
        email="test@chainfactor.ai",
        phone="+919876543210",
        company_name="Test Corp Pvt Ltd",
        gstin="27AABCT1234R1ZM",
        wallet_address=None,
    )
    merged = await db_session.merge(user)
    await db_session.flush()
    return merged


@pytest.fixture
async def test_user_with_wallet(db_session: AsyncSession) -> User:
    """Create a test user with a linked wallet."""
    user = User(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        cognito_sub="test-cognito-sub-002",
        name="Wallet User",
        email="wallet@chainfactor.ai",
        phone="+919876543211",
        company_name="Wallet Corp Pvt Ltd",
        gstin="29AABCW5678R1ZX",
        wallet_address="ALGO7TEST2ADDRESS3FOR4UNIT5TESTING6WALLET7X4F2",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def client(db_session: AsyncSession, test_user: User):
    """Async HTTP test client with mocked auth (returns test_user)."""
    from app.database import get_db
    from app.main import app
    from app.modules.auth.dependencies import get_current_user

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client(db_session: AsyncSession):
    """Async HTTP test client WITHOUT auth override (for testing auth flows)."""
    from app.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
