from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from starlette.requests import Request

from taskapp.infrastructure.rate_limit import user_or_address_key
from taskapp.infrastructure.security import JwtTokenService
from tests.fakes import FixedClock

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"
NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def request(authorization: str | None = None, ip: str = "10.0.0.7") -> Request:
    headers = [(b"authorization", authorization.encode())] if authorization else []
    return Request({"type": "http", "headers": headers, "client": (ip, 5000)})


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def tokens(clock: FixedClock) -> JwtTokenService:
    return JwtTokenService(SECRET, clock)


async def test_ac02_a_valid_token_is_counted_against_its_user(tokens: JwtTokenService) -> None:
    user_id = uuid4()
    token = (await tokens.issue(user_id)).token

    key = user_or_address_key(tokens)(request(f"Bearer {token}"))

    assert key == f"user:{user_id}"


async def test_ac02_the_scheme_is_matched_without_regard_to_case(tokens: JwtTokenService) -> None:
    user_id = uuid4()
    token = (await tokens.issue(user_id)).token

    assert user_or_address_key(tokens)(request(f"bearer {token}")) == f"user:{user_id}"


def test_ac02_a_request_without_a_token_is_counted_against_its_address(
    tokens: JwtTokenService,
) -> None:
    assert user_or_address_key(tokens)(request()) == "ip:10.0.0.7"


@pytest.mark.parametrize("header", ["Bearer", "Bearer ", "Bearer garbage", "Basic YTpi", "token"])
def test_ac02_a_malformed_authorization_header_falls_back_to_the_address(
    tokens: JwtTokenService, header: str
) -> None:
    assert user_or_address_key(tokens)(request(header)) == "ip:10.0.0.7"


async def test_ac02_a_forged_token_falls_back_to_the_address(tokens: JwtTokenService) -> None:
    victim = uuid4()
    now = int(NOW.timestamp())
    forged = jwt.encode(
        {"sub": str(victim), "iat": now, "exp": now + 1800},
        "an-attackers-own-secret-of-sufficient-length",
        algorithm="HS256",
    )

    assert user_or_address_key(tokens)(request(f"Bearer {forged}")) == "ip:10.0.0.7"


async def test_ac02_an_expired_token_falls_back_to_the_address(
    tokens: JwtTokenService, clock: FixedClock
) -> None:
    token = (await tokens.issue(uuid4())).token
    clock.set(NOW + timedelta(hours=1))

    assert user_or_address_key(tokens)(request(f"Bearer {token}")) == "ip:10.0.0.7"
