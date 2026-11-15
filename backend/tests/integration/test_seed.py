from datetime import UTC, datetime, timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.domain.status import TERMINAL_STATUSES, TaskStatus
from taskapp.seed import DEMO_PASSWORD, DEMO_USERS, SeedOutcome, SeedSettings, run, seed


async def rows(engine: AsyncEngine, sql: str) -> list[Any]:
    async with engine.connect() as connection:
        return list((await connection.execute(text(sql))).all())


async def test_ac06_seeding_an_empty_database_creates_three_demo_users(
    engine: AsyncEngine, test_database_url: str
) -> None:
    outcome = await seed(test_database_url)

    assert outcome is SeedOutcome.SEEDED
    users = await rows(engine, "SELECT email, name FROM users ORDER BY email")
    assert [(u.email, u.name) for u in users] == [(email, name) for email, name in DEMO_USERS]


async def test_ac06_the_tasks_cover_every_status_and_both_overdue_and_upcoming_dates(
    engine: AsyncEngine, test_database_url: str
) -> None:
    await seed(test_database_url)

    tasks = await rows(engine, "SELECT status, due_date, creator_id, assignee_id FROM tasks")
    now = datetime.now(UTC)
    open_tasks = [t for t in tasks if TaskStatus(t.status) not in TERMINAL_STATUSES]
    overdue = [t for t in open_tasks if t.due_date and t.due_date < now]
    upcoming = [t for t in open_tasks if t.due_date and now < t.due_date < now + timedelta(days=30)]
    assert 12 <= len(tasks) <= 18
    assert {t.status for t in tasks} == {status.value for status in TaskStatus}
    assert len(overdue) >= 3
    assert len(upcoming) >= 3
    assert any(t.due_date is None for t in tasks)
    assert any(t.assignee_id is None for t in tasks)
    assert len({t.creator_id for t in tasks}) == 3
    assert len({t.assignee_id for t in tasks if t.assignee_id}) == 3


async def test_ac06_every_demo_user_can_log_in_with_the_documented_credentials(
    client: AsyncClient, test_database_url: str
) -> None:
    await seed(test_database_url)

    for email, _name in DEMO_USERS:
        response = await client.post(
            "/auth/login", json={"email": email, "password": DEMO_PASSWORD}
        )
        assert response.status_code == 200, email
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        listing = await client.get("/tasks?size=100", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["total"] > 0


async def test_ac07_seeding_again_adds_and_changes_nothing(
    engine: AsyncEngine, test_database_url: str
) -> None:
    await seed(test_database_url)
    before = await rows(engine, "SELECT id, status, updated_at FROM tasks ORDER BY id")
    users_before = await rows(engine, "SELECT id FROM users ORDER BY id")

    outcome = await seed(test_database_url)

    assert outcome is SeedOutcome.ALREADY_SEEDED
    assert await rows(engine, "SELECT id, status, updated_at FROM tasks ORDER BY id") == before
    assert await rows(engine, "SELECT id FROM users ORDER BY id") == users_before


async def test_ac07_the_command_says_when_the_data_is_already_there(
    engine: AsyncEngine, test_database_url: str
) -> None:
    said: list[str] = []
    settings = SeedSettings(database_url=test_database_url)

    first = await run(settings, said.append)
    second = await run(settings, said.append)

    assert (first, second) == (0, 0)
    assert "seeded" in said[0].lower()
    assert "already" in said[1].lower()


async def test_ac08_the_command_refuses_to_run_in_production_and_changes_nothing(
    engine: AsyncEngine, test_database_url: str
) -> None:
    said: list[str] = []

    code = await run(
        SeedSettings(database_url=test_database_url, environment="production"), said.append
    )

    assert code != 0
    assert "production" in said[0].lower()
    assert await rows(engine, "SELECT id FROM users") == []
    assert await rows(engine, "SELECT id FROM tasks") == []
