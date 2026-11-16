from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from taskapp.api.rate_limit import install_rate_limit
from taskapp.composition import build_app_limiter
from taskapp.infrastructure.security import JwtTokenService, SystemClock
from taskapp.infrastructure.settings import Settings

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"


async def test_ac02_the_application_limiter_keys_requests_by_signed_in_user() -> None:
    settings = Settings(
        jwt_secret=SECRET,  # type: ignore[arg-type]
        redis_url="memory://",
        rate_limit_default="2/minute",
    )
    app = FastAPI()
    install_rate_limit(app, build_app_limiter(settings))

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    tokens = JwtTokenService(SECRET, SystemClock())
    first = {"Authorization": f"Bearer {(await tokens.issue(uuid4())).token}"}
    second = {"Authorization": f"Bearer {(await tokens.issue(uuid4())).token}"}
    transport = ASGITransport(app=app, client=("10.0.0.1", 5000))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        one = [(await client.get("/ping", headers=first)).status_code for _ in range(3)]
        two = [(await client.get("/ping", headers=second)).status_code for _ in range(3)]

    assert one == [200, 200, 429]
    assert two == [200, 200, 429]


def test_ac05_the_notifier_publishes_through_the_fail_fast_app() -> None:
    from taskapp.composition import build_dependencies

    settings = Settings(jwt_secret=SECRET)  # type: ignore[arg-type]

    notifier = build_dependencies(settings).notifier

    options = notifier._task.app.conf.broker_transport_options  # type: ignore[attr-defined]
    assert options["socket_connect_timeout"] <= 0.5
