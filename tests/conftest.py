import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.database import get_async_session
import app.db.models  # noqa: F401
from config import settings
from main import app


try:
    import pytest_asyncio

    async_fixture = pytest_asyncio.fixture
except Exception:  # noqa: BLE001
    async_fixture = pytest.fixture


@async_fixture
async def db_session_factory(tmp_path):
    db_file = tmp_path / "test_epic02.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield session_factory
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture
def override_db_dependency(db_session_factory):
    async def _override():
        async with db_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_session] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_async_session, None)


@pytest.fixture(autouse=True)
def disable_external_http_calls(monkeypatch):
    """Disable outbound HTTP integrations in tests by default."""
    monkeypatch.setattr(settings, "location_service_base_url", "")
    monkeypatch.setattr(settings, "schedule_provider_base_url", "")
