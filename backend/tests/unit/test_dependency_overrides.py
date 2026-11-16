from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from taskapp.api.app import create_app
from taskapp.api.dependencies import Dependencies, get_dependencies
from taskapp.infrastructure.rate_limit import build_limiter
from tests.fakes import (
    FakePasswordHasher,
    FakeTokenService,
    FixedClock,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
    RecordingNotifier,
)


def fake_dependencies() -> Dependencies:
    return Dependencies(
        uow_factory=lambda: InMemoryUnitOfWork(InMemoryTaskRepository(), InMemoryUserRepository()),
        hasher=FakePasswordHasher(),
        tokens=FakeTokenService(),
        clock=FixedClock(datetime(2026, 1, 15, tzinfo=UTC)),
        notifier=RecordingNotifier(),
    )


async def test_ac02_dependency_overrides_work_on_every_route() -> None:
    # Routes are registered straight on the app (so the rate limiter can see them); FastAPI's
    # dependency overrides must still reach them.
    app = create_app(limiter=build_limiter("100/minute", "memory://"))
    app.dependency_overrides[get_dependencies] = fake_dependencies
    transport = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        users = await client.get("/users")
        tasks = await client.get("/tasks")

    assert users.status_code == 401  # reached the handler, which rejects the missing token
    assert tasks.status_code == 401
