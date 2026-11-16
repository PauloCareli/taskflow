from collections.abc import AsyncIterator
from dataclasses import dataclass

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.rate_limit import build_limiter, user_or_address_key
from taskapp.infrastructure.security import JwtTokenService, SystemClock
from taskapp.infrastructure.settings import Settings
from tests.integration.conftest import API_SECRET

IP = "10.0.0.1"


@dataclass
class World:
    limited: FastAPI
    alice_token: str
    bob_token: str
    alice_id: str


def client_for(app: FastAPI, ip: str = IP) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app, client=(ip, 5000)), base_url="http://test")


async def sign_up(plain: FastAPI, name: str) -> tuple[str, str]:
    email = f"{name}@example.com"
    async with client_for(plain, "10.9.9.9") as client:
        await client.post(
            "/auth/register", json={"email": email, "name": name, "password": "password123"}
        )
        login = await client.post("/auth/login", json={"email": email, "password": "password123"})
        token = login.json()["access_token"]
        me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


@pytest.fixture
async def world(test_database_url: str, engine: AsyncEngine) -> AsyncIterator[World]:
    """Two signed-up users, and an app that allows 3 requests per minute per rate-limit key."""
    settings = Settings(
        database_url=test_database_url,
        jwt_secret=API_SECRET,  # type: ignore[arg-type]
        celery_eager=True,
    )
    dependencies = build_dependencies(settings)
    plain = create_app(dependencies=dependencies)
    alice_token, alice_id = await sign_up(plain, "alice")
    bob_token, _ = await sign_up(plain, "bob")
    tokens = JwtTokenService(API_SECRET, SystemClock())
    limited = create_app(
        dependencies=dependencies,
        limiter=build_limiter("3/minute", "memory://", key_func=user_or_address_key(tokens)),
    )
    yield World(limited, alice_token, bob_token, alice_id)
    if dependencies.shutdown:
        await dependencies.shutdown()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def statuses(client: AsyncClient, token: str | None, n: int) -> list[int]:
    headers = bearer(token) if token else {}
    return [(await client.get("/users", headers=headers)).status_code for _ in range(n)]


async def test_ac02_two_users_behind_one_address_have_separate_budgets(world: World) -> None:
    async with client_for(world.limited) as client:
        alice = await statuses(client, world.alice_token, 4)
        bob = await statuses(client, world.bob_token, 4)

    assert alice == [200, 200, 200, 429]
    assert bob == [200, 200, 200, 429]


async def test_ac02_anonymous_requests_are_counted_per_address(world: World) -> None:
    async with (
        client_for(world.limited, "10.0.0.1") as first,
        client_for(world.limited, "10.0.0.2") as second,
    ):
        blocked = await statuses(first, None, 4)
        other = await statuses(second, None, 1)

    assert blocked == [401, 401, 401, 429]
    assert other == [401]


async def test_ac02_an_anonymous_flood_does_not_use_up_a_signed_in_users_budget(
    world: World,
) -> None:
    async with client_for(world.limited) as client:
        await statuses(client, None, 4)
        alice = await statuses(client, world.alice_token, 3)

    assert alice == [200, 200, 200]


async def test_ac02_a_forged_token_cannot_spend_or_dodge_another_users_budget(
    world: World,
) -> None:
    now = 2_000_000_000
    forged = jwt.encode(
        {"sub": world.alice_id, "iat": now - 10, "exp": now},
        "an-attackers-own-secret-of-sufficient-length",
        algorithm="HS256",
    )
    async with client_for(world.limited) as client:
        await statuses(client, world.alice_token, 4)  # Alice is now over her limit
        by_forger = await statuses(client, forged, 3)
        alice_again = await statuses(client, world.alice_token, 1)

    assert by_forger == [401, 401, 401]  # counted against the address, not against Alice
    assert alice_again == [429]
