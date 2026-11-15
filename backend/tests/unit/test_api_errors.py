from httpx import ASGITransport, AsyncClient

from taskapp.api.app import create_app
from taskapp.api.dependencies import Dependencies
from taskapp.application.ports import UnitOfWork
from tests.fakes import FakePasswordHasher, FakeTokenService


def database_down() -> UnitOfWork:
    raise ConnectionError("password authentication failed for user taskflow")


async def test_ac05_an_unexpected_failure_is_a_500_with_the_uniform_body_and_no_internals() -> None:
    app = create_app(
        dependencies=Dependencies(
            uow_factory=database_down, hasher=FakePasswordHasher(), tokens=FakeTokenService()
        )
    )
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login", json={"email": "alice@example.com", "password": "s3cret-pass"}
        )

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong", "details": []}
    }
    assert "password authentication" not in response.text
