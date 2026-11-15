import asyncio
import os
import secrets
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.db.session import create_session_factory
from taskapp.infrastructure.settings import DEFAULT_DATABASE_URL, Settings

API_SECRET = secrets.token_urlsafe(32)
BACKEND_DIR = Path(__file__).resolve().parents[2]
SERVER_URL = os.environ.get("TASKAPP_DATABASE_URL", DEFAULT_DATABASE_URL)


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


async def _admin_execute(statement: str) -> None:
    admin = create_async_engine(SERVER_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        async with admin.connect() as connection:
            await connection.execute(text(statement))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session")
def test_database_url() -> Iterator[str]:
    """A throwaway database on the configured server, built from empty by the migrations."""
    name = f"taskflow_test_{os.getpid()}"
    asyncio.run(_admin_execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    asyncio.run(_admin_execute(f'CREATE DATABASE "{name}"'))
    url = make_url(SERVER_URL).set(database=name).render_as_string(hide_password=False)
    try:
        command.upgrade(alembic_config(url), "head")
        yield url
    finally:
        asyncio.run(_admin_execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture
async def engine(test_database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(test_database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE tasks, users CASCADE"))
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(test_database_url: str, engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """The whole app (routes, auth, SQL) on the throwaway database, called in-process."""
    settings = Settings(database_url=test_database_url, jwt_secret=API_SECRET)  # type: ignore[arg-type]
    dependencies = build_dependencies(settings)
    app = create_app(dependencies=dependencies)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    if dependencies.shutdown:
        await dependencies.shutdown()
