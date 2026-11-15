import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.infrastructure.security import JwtTokenService
from tests.fakes import FixedClock
from tests.integration.conftest import API_SECRET

SECRET = API_SECRET
PASSWORD = "s3cret-pass"
ALICE = {"email": "alice@example.com", "name": "Alice", "password": PASSWORD}


async def register(client: AsyncClient, **overrides: str) -> Response:
    return await client.post("/auth/register", json={**ALICE, **overrides})


async def login(
    client: AsyncClient, email: str = "alice@example.com", password: str = PASSWORD
) -> Response:
    return await client.post("/auth/login", json={"email": email, "password": password})


async def token_for(client: AsyncClient) -> str:
    await register(client)
    return str((await login(client)).json()["access_token"])


def assert_uniform_error(response: Response, status: int, code: str) -> None:
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str)
    assert isinstance(error["details"], list)


async def test_ac01_register_returns_the_new_user_without_any_secret(client: AsyncClient) -> None:
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "name"}
    assert (body["email"], body["name"]) == ("alice@example.com", "Alice")
    assert PASSWORD not in response.text


async def test_ac01_the_stored_password_is_an_argon2_hash(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    await register(client)

    async with engine.connect() as connection:
        stored = (await connection.execute(text("SELECT password_hash FROM users"))).scalar_one()

    assert stored.startswith("$argon2")
    assert PASSWORD not in stored


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"name": ""},
        {"password": "short"},
    ],
)
async def test_ac02_invalid_registration_is_a_422_with_the_uniform_body_and_stores_nothing(
    client: AsyncClient, engine: AsyncEngine, overrides: dict[str, str]
) -> None:
    response = await register(client, **overrides)

    assert_uniform_error(response, 422, "validation_error")
    async with engine.connect() as connection:
        count = (await connection.execute(text("SELECT count(*) FROM users"))).scalar_one()
    assert count == 0


async def test_ac02_a_missing_field_is_a_422_with_the_uniform_body(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={"email": "alice@example.com"})

    assert_uniform_error(response, 422, "validation_error")
    assert response.json()["error"]["details"]


async def test_ac02_a_duplicate_email_in_any_case_is_a_409_and_the_original_is_unchanged(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    await register(client)

    response = await register(client, email="ALICE@Example.com", name="Impostor")

    assert_uniform_error(response, 409, "email_taken")
    async with engine.connect() as connection:
        rows = (await connection.execute(text("SELECT name FROM users"))).all()
    assert [row.name for row in rows] == ["Alice"]


async def test_ac03_login_returns_a_bearer_token_that_lasts_30_minutes(
    client: AsyncClient,
) -> None:
    await register(client)

    response = await login(client)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800


async def test_ac03_login_matches_the_email_in_any_case_and_ignores_surrounding_spaces(
    client: AsyncClient,
) -> None:
    await register(client)

    assert (await login(client, email="  ALICE@example.com ")).status_code == 200


async def test_ac03_the_login_token_opens_the_protected_route(client: AsyncClient) -> None:
    token = await token_for(client)

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "name"}
    assert body["email"] == "alice@example.com"


async def test_ac04_unknown_email_and_wrong_password_get_the_same_401(
    client: AsyncClient,
) -> None:
    await register(client)

    unknown = await login(client, email="nobody@example.com")
    wrong = await login(client, password="wrong-password")

    assert_uniform_error(unknown, 401, "invalid_credentials")
    assert_uniform_error(wrong, 401, "invalid_credentials")
    assert unknown.json() == wrong.json()


async def test_ac04_login_with_a_missing_field_is_a_422(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={"email": "alice@example.com"})

    assert_uniform_error(response, 422, "validation_error")


def b64(data: dict[str, object]) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


async def expired_token(client: AsyncClient) -> str:
    me = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {await token_for(client)}"}
    )
    user_id = me.json()["id"]
    old = FixedClock(datetime.now(UTC) - timedelta(hours=2))
    return (await JwtTokenService(SECRET, old).issue(user_id)).token


async def test_ac05_a_request_without_a_token_is_a_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert_uniform_error(response, 401, "invalid_token")
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "header",
    ["Bearer garbage", "Bearer ", "Basic YWxpY2U6cGFzcw==", "Token abc", "Bearer a.b.c"],
)
async def test_ac05_a_malformed_authorization_header_is_a_401(
    client: AsyncClient, header: str
) -> None:
    response = await client.get("/auth/me", headers={"Authorization": header})

    assert_uniform_error(response, 401, "invalid_token")


async def test_ac05_an_expired_token_is_a_401(client: AsyncClient) -> None:
    token = await expired_token(client)

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert_uniform_error(response, 401, "invalid_token")


async def test_ac05_a_token_signed_with_another_secret_is_a_401(client: AsyncClient) -> None:
    await register(client)
    now = int(datetime.now(UTC).timestamp())
    claims = {"sub": str(uuid4()), "iat": now, "exp": now + 1800}
    forged = jwt.encode(claims, "some-other-secret-that-is-long-enough-xx", algorithm="HS256")

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert_uniform_error(response, 401, "invalid_token")


async def test_ac05_a_tampered_token_and_an_unsigned_token_are_rejected(
    client: AsyncClient,
) -> None:
    token = await token_for(client)
    header, _payload, signature = token.split(".")
    now = int(datetime.now(UTC).timestamp())
    claims = {"sub": str(uuid4()), "iat": now, "exp": now + 1800}
    tampered = f"{header}.{b64(claims)}.{signature}"
    unsigned = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(claims)}."

    for bad in (tampered, unsigned):
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {bad}"})
        assert_uniform_error(response, 401, "invalid_token")


async def test_ac05_a_token_for_a_user_that_no_longer_exists_is_a_401(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    token = await token_for(client)
    async with engine.begin() as connection:
        await connection.execute(text("DELETE FROM users"))

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert_uniform_error(response, 401, "invalid_token")


@pytest.mark.parametrize("overrides", [{"email": "a\x00b@example.com"}, {"name": "A\x00"}])
async def test_ac02_registration_with_a_control_character_is_a_422_not_a_server_error(
    client: AsyncClient, overrides: dict[str, str]
) -> None:
    response = await register(client, **overrides)

    assert_uniform_error(response, 422, "validation_error")


async def test_ac04_login_with_an_email_that_can_never_exist_gets_the_generic_401(
    client: AsyncClient,
) -> None:
    await register(client)

    response = await login(client, email="alice\x00@example.com")

    assert_uniform_error(response, 401, "invalid_credentials")


async def test_health_stays_public(client: AsyncClient) -> None:
    assert (await client.get("/health")).json() == {"status": "ok"}
