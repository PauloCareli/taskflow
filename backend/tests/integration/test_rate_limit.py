import asyncio

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
        await asyncio.sleep(1.1)
        assert (await client.get("/ping")).status_code == 200


async def test_ac01_health_is_exempt_from_the_limit() -> None:
    async with client_for(make_app("1/minute")) as client:
        statuses = [(await client.get("/health")).status_code for _ in range(5)]

    assert statuses == [200] * 5


async def test_ac05_requests_are_served_when_the_storage_is_unreachable() -> None:
    async with client_for(make_app("1/minute", UNREACHABLE_REDIS)) as client:
        statuses = [(await client.get("/ping")).status_code for _ in range(3)]

    assert statuses == [200, 200, 200]
