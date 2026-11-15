import asyncio
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from taskapp.api.app import create_app
from taskapp.infrastructure.rate_limit import build_limiter

UNREACHABLE_REDIS = "redis://127.0.0.1:1/0"


def make_app(limit: str, storage_uri: str = "memory://") -> FastAPI:
    app = create_app(limiter=build_limiter(limit, storage_uri))

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    return app


def client_for(app: FastAPI, ip: str = "10.0.0.1") -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app, client=(ip, 5000)), base_url="http://test")


async def test_ac01_requests_over_the_limit_get_429() -> None:
    async with client_for(make_app("3/minute")) as client:
        statuses = [(await client.get("/ping")).status_code for _ in range(4)]

    assert statuses == [200, 200, 200, 429]


async def test_ac02_a_429_uses_the_uniform_error_body_and_retry_after() -> None:
    async with client_for(make_app("1/minute")) as client:
        await client.get("/ping")
        response = await client.get("/ping")

    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "rate_limited"
    assert body["error"]["message"]
    assert body["error"]["details"] == []
    assert set(body) == {"error"}
    retry_after = response.headers["retry-after"]
    assert retry_after.isdigit()
    assert 1 <= int(retry_after) <= 60


async def test_ac03_each_client_ip_has_its_own_budget() -> None:
    app = make_app("1/minute")
    async with client_for(app, "10.0.0.1") as first, client_for(app, "10.0.0.2") as second:
        await first.get("/ping")
        blocked = await first.get("/ping")
        other = await second.get("/ping")

    assert blocked.status_code == 429
    assert other.status_code == 200


async def test_ac03_a_client_is_served_again_after_the_window_elapsed() -> None:
    async with client_for(make_app("1/second")) as client:
        await client.get("/ping")
        assert (await client.get("/ping")).status_code == 429
        await asyncio.sleep(1.25)
        assert (await client.get("/ping")).status_code == 200


async def test_ac01_health_is_exempt_from_the_limit() -> None:
    async with client_for(make_app("1/minute")) as client:
        statuses = [(await client.get("/health")).status_code for _ in range(5)]

    assert statuses == [200] * 5


async def test_ac05_requests_are_served_when_the_storage_is_unreachable() -> None:
    async with client_for(make_app("1/minute", UNREACHABLE_REDIS)) as client:
        statuses = [(await client.get("/ping")).status_code for _ in range(3)]

    assert statuses == [200, 200, 200]


async def test_ac01_forwarded_for_headers_do_not_change_the_client_key() -> None:
    async with client_for(make_app("2/minute")) as client:
        statuses = [
            (await client.get("/ping", headers={"X-Forwarded-For": f"203.0.113.{n}"})).status_code
            for n in range(3)
        ]

    assert statuses == [200, 200, 429]


async def test_ac02_a_429_is_still_answered_when_the_storage_fails_afterwards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = make_app("1/minute")

    def broken(*args: Any, **kwargs: Any) -> None:
        raise ConnectionError("storage went away")

    async with client_for(app) as client:
        await client.get("/ping")
        monkeypatch.setattr(app.state.limiter.limiter, "get_window_stats", broken)
        response = await client.get("/ping")

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) >= 1


def test_ac05_the_redis_storage_gives_up_quickly_instead_of_hanging_requests() -> None:
    limiter = build_limiter("1/minute", "redis://127.0.0.1:1/0")
    storage: Any = limiter.limiter.storage
    options = storage.storage.connection_pool.connection_kwargs

    assert options["socket_connect_timeout"] <= 0.5
    assert options["socket_timeout"] <= 0.5
