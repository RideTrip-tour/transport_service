import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
@pytest.mark.integration
async def test_epic02_upgrade_and_downgrade_smoke():
    db_url_raw = os.getenv("TEST_DATABASE_URL")
    if not db_url_raw:
        pytest.skip("Set TEST_DATABASE_URL to run migration smoke tests")

    repo_root = Path(__file__).resolve().parents[1]
    db_url = make_url(db_url_raw)
    env = os.environ.copy()
    env.update(
        {
            "DB_DRIVER": f"{db_url.drivername}",
            "DB_HOST": db_url.host or "localhost",
            "DB_PORT": str(db_url.port or 5432),
            "DB_NAME": db_url.database or "",
            "DB_USER": db_url.username or "",
            "DB_PASS": db_url.password or "",
        }
    )

    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        check=True,
    )

    async_url = db_url
    if not async_url.drivername.startswith("postgresql+asyncpg"):
        async_url = async_url.set(drivername="postgresql+asyncpg")
    engine = create_async_engine(async_url)

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
        tables = {row[0] for row in result.all()}

    assert {"segments", "routes", "search_history"}.issubset(tables)
    assert "transport_types" not in tables
    assert "transport_requests" not in tables
    assert "transport_catalog_routes" not in tables
    assert "transport_quotes" not in tables

    subprocess.run(
        ["alembic", "downgrade", "-1"],
        cwd=repo_root,
        env=env,
        check=True,
    )

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
        downgraded_tables = {row[0] for row in result.all()}
    assert "transport_types" in downgraded_tables
    assert "transport_requests" in downgraded_tables
    assert "transport_catalog_routes" in downgraded_tables
    assert "transport_quotes" in downgraded_tables
    await engine.dispose()
