from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.rate_limit import build_limiter
from taskapp.infrastructure.settings import Settings
from tests.integration.conftest import API_SECRET

BODY = {"email": "alice@example.com", "name": "Alice", "password": "password123"}


@pytest.fixture
async def app(test_database_url: str, engine: AsyncEngine) -> AsyncIterator[FastAPI]:
    """The real app with a 100/minute default and a 3/minute limit on login and register."""
    settings = Settings(
        database_url=test_database_url,
        jwt_secret=API_SECRET,  # type: ignore[arg-type]
        celery_eager=True,
    )
    dependencies = build_dependencies(settings)
    yield create_app(
        dependencies=dependencies,
        limiter=build_limiter("100/minute", "memory://"),
        auth_limit="3/minute",
    )
    if dependencies.shutdown:
        await dependencies.shutdown()


def client_for(app: FastAPI, ip: str = "10.0.0.1") -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app, client=(ip, 5000)), base_url="http://test")


async def login(client: AsyncClient) -> Response:
    return await client.post("/auth/login", json={"email": BODY["email"], "password": "wrong"})


async def register(client: AsyncClient, n: int) -> Response:
    return await client.post("/auth/register", json={**BODY, "email": f"user{n}@example.com"})


async def test_ac01_login_over_the_authentication_limit_gets_429(app: FastAPI) -> None:
    async with client_for(app) as client:
        statuses = [(await login(client)).status_code for _ in range(4)]

    assert statuses == [401, 401, 401, 429]


async def test_ac01_register_over_the_authentication_limit_gets_429(app: FastAPI) -> None:
    async with client_for(app) as client:
        statuses = [(await register(client, n)).status_code for n in range(4)]

    assert statuses == [201, 201, 201, 429]


async def test_ac01_the_429_has_the_uniform_body_and_retry_after(app: FastAPI) -> None:
    async with client_for(app) as client:
        for _ in range(3):
            await login(client)
        response = await login(client)

    assert response.status_code == 429
    error = response.json()["error"]
    assert (error["code"], error["details"]) == ("rate_limited", [])
    assert 1 <= int(response.headers["retry-after"]) <= 60


async def test_ac01_each_route_has_its_own_authentication_budget(app: FastAPI) -> None:
    async with client_for(app) as client:
        for _ in range(4):
            await login(client)
        registered = await register(client, 0)

    assert registered.status_code == 201


async def test_ac01_other_endpoints_keep_the_default_limit(app: FastAPI) -> None:
    async with client_for(app) as client:
        for _ in range(4):
            await login(client)
        statuses = {(await client.get("/auth/me")).status_code for _ in range(5)}
        health = await client.get("/health")

    assert statuses == {401}
    assert health.status_code == 200


async def test_ac01_each_client_address_has_its_own_authentication_budget(app: FastAPI) -> None:
    async with client_for(app, "10.0.0.1") as first, client_for(app, "10.0.0.2") as second:
        for _ in range(4):
            await login(first)
        other = await login(second)

    assert other.status_code == 401
