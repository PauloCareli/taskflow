import logging
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.settings import Settings
from tests.integration.conftest import API_SECRET

UNREACHABLE_BROKER = "redis://127.0.0.1:1/0"
PASSWORD = "password123"


@pytest.fixture
async def client(test_database_url: str, engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """The real app, with a message broker that nobody is listening on."""
    settings = Settings(
        database_url=test_database_url,
        jwt_secret=API_SECRET,  # type: ignore[arg-type]
        redis_url=UNREACHABLE_BROKER,
        celery_eager=False,
    )
    dependencies = build_dependencies(settings)
    app = create_app(dependencies=dependencies)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    if dependencies.shutdown:
        await dependencies.shutdown()


async def sign_up(client: AsyncClient, name: str) -> tuple[dict[str, str], str]:
    email = f"{name}@example.com"
    await client.post("/auth/register", json={"email": email, "name": name, "password": PASSWORD})
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return headers, (await client.get("/auth/me", headers=headers)).json()["id"]


async def test_ac05_assigning_still_succeeds_and_is_stored_when_the_broker_is_down(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    alice, _ = await sign_up(client, "alice")
    _, bob_id = await sign_up(client, "bob")
    task = (await client.post("/tasks", json={"title": "Review"}, headers=alice)).json()

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        response = await client.post(
            f"/tasks/{task['id']}/assign", json={"assignee_id": bob_id}, headers=alice
        )

    assert response.status_code == 200
    stored = (await client.get(f"/tasks/{task['id']}", headers=alice)).json()
    assert stored["assignee"]["id"] == bob_id
    errors = [r for r in caplog.records if r.name == "taskapp.notifications" and r.levelno >= 40]
    assert len(errors) == 1
    assert task["id"] in errors[0].getMessage()


async def test_ac05_creating_a_task_with_an_assignee_succeeds_when_the_broker_is_down(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    alice, _ = await sign_up(client, "alice")
    _, bob_id = await sign_up(client, "bob")

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        response = await client.post(
            "/tasks", json={"title": "Review", "assignee_id": bob_id}, headers=alice
        )

    assert response.status_code == 201
    assert response.json()["assignee"]["id"] == bob_id
    assert [r for r in caplog.records if r.name == "taskapp.notifications" and r.levelno >= 40]
