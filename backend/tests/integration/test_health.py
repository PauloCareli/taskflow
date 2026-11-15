from httpx import ASGITransport, AsyncClient

from taskapp.api.app import create_app
from taskapp.main import app as main_app


async def test_health_returns_ok() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_main_app_serves_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=main_app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
