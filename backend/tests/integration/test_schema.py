import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.infrastructure.db.models import Base
from tests.integration.conftest import alembic_config

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


async def insert_user(engine: AsyncEngine, email: str, user_id: UUID | None = None) -> UUID:
    user_id = user_id or uuid4()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO users (id, email, name, password_hash, created_at) "
                "VALUES (:id, :email, 'Name', 'hash', :now)"
            ),
            {"id": user_id, "email": email, "now": NOW},
        )
    return user_id


async def insert_task(engine: AsyncEngine, creator_id: UUID, assignee_id: UUID | None) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tasks (id, title, status, creator_id, assignee_id, created_at, "
                "updated_at) VALUES (:id, 'T', 'todo', :creator, :assignee, :now, :now)"
            ),
            {"id": uuid4(), "creator": creator_id, "assignee": assignee_id, "now": NOW},
        )


async def test_ac08_migrations_create_the_schema_from_an_empty_database(
    engine: AsyncEngine,
) -> None:
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda c: set(inspect(c).get_table_names()))

    assert {"users", "tasks", "alembic_version"} <= tables
    assert {"users", "tasks"} <= set(Base.metadata.tables)


async def test_ac08_the_migrated_schema_matches_the_models(engine: AsyncEngine) -> None:
    def differences(connection: Connection) -> list[object]:
        context = MigrationContext.configure(connection)
        return list(compare_metadata(context, Base.metadata))

    async with engine.connect() as connection:
        assert await connection.run_sync(differences) == []


async def test_ac08_migrations_can_be_reverted_and_applied_again(
    test_database_url: str, engine: AsyncEngine
) -> None:
    config = alembic_config(test_database_url)

    await asyncio.to_thread(command.downgrade, config, "base")
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert tables.isdisjoint({"users", "tasks"})

    await asyncio.to_thread(command.upgrade, config, "head")
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda c: set(inspect(c).get_table_names()))
    assert {"users", "tasks"} <= tables


async def test_ac07_email_is_unique_regardless_of_letter_case(engine: AsyncEngine) -> None:
    await insert_user(engine, "alice@example.com")

    with pytest.raises(IntegrityError):
        await insert_user(engine, "ALICE@Example.com")


async def test_ac07_a_task_must_reference_an_existing_creator(engine: AsyncEngine) -> None:
    with pytest.raises(IntegrityError):
        await insert_task(engine, creator_id=uuid4(), assignee_id=None)


async def test_ac07_a_task_must_reference_an_existing_assignee(engine: AsyncEngine) -> None:
    creator = await insert_user(engine, "alice@example.com")

    with pytest.raises(IntegrityError):
        await insert_task(engine, creator_id=creator, assignee_id=uuid4())


async def test_ac07_the_filter_columns_are_indexed(engine: AsyncEngine) -> None:
    def indexed_columns(connection: Connection) -> set[str]:
        return {
            column
            for index in inspect(connection).get_indexes("tasks")
            for column in index["column_names"][:1]
            if column
        }

    async with engine.connect() as connection:
        leading = await connection.run_sync(indexed_columns)

    assert {"status", "due_date", "assignee_id", "creator_id"} <= leading
