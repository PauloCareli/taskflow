import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from taskapp.domain.errors import InvalidToken
from taskapp.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from tests.fakes import FixedClock

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"
NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def make_service(clock: FixedClock, secret: str = SECRET) -> JwtTokenService:
    return JwtTokenService(secret, clock)


def b64(data: dict[str, object]) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


async def test_ac01_the_hash_is_argon2_salted_and_verifies_only_the_right_password() -> None:
    hasher = Argon2PasswordHasher()

    first = await hasher.hash("s3cret-pass")
    second = await hasher.hash("s3cret-pass")

    assert first.startswith("$argon2")
    assert "s3cret-pass" not in first
    assert first != second
    assert await hasher.verify("s3cret-pass", first) is True
    assert await hasher.verify("wrong-pass", first) is False


async def test_ac03_a_token_carries_the_user_and_lasts_30_minutes() -> None:
    clock = FixedClock(NOW)
    user_id = uuid4()

    token = await make_service(clock).issue(user_id)

    assert token.expires_in == 1800
    claims = jwt.decode(
        token.token,
        SECRET,
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_iat": False},
    )
    assert claims["sub"] == str(user_id)
    assert claims["iat"] == int(NOW.timestamp())
    assert claims["exp"] == int(NOW.timestamp()) + 1800
    assert await make_service(clock).verify(token.token) == user_id


async def test_ac03_a_token_is_accepted_until_30_minutes_and_rejected_after() -> None:
    clock = FixedClock(NOW)
    service = make_service(clock)
    user_id = uuid4()
    token = (await service.issue(user_id)).token

    clock.set(NOW + timedelta(seconds=1799))
    assert await service.verify(token) == user_id

    clock.set(NOW + timedelta(seconds=1800))
    with pytest.raises(InvalidToken):
        await service.verify(token)


async def test_ac05_malformed_tokens_are_rejected() -> None:
    service = make_service(FixedClock(NOW))

    for bad in ["", "garbage", "a.b.c", "Bearer abc"]:
        with pytest.raises(InvalidToken):
            await service.verify(bad)


async def test_ac05_a_token_signed_with_another_secret_is_rejected() -> None:
    clock = FixedClock(NOW)
    forged = (
        await make_service(clock, "another-secret-of-sufficient-length-xx").issue(uuid4())
    ).token

    with pytest.raises(InvalidToken):
        await make_service(clock).verify(forged)


async def test_ac05_a_token_with_an_altered_payload_is_rejected() -> None:
    clock = FixedClock(NOW)
    service = make_service(clock)
    header, _payload, signature = (await service.issue(uuid4())).token.split(".")
    altered = b64(
        {"sub": str(uuid4()), "iat": int(NOW.timestamp()), "exp": int(NOW.timestamp()) + 1800}
    )

    with pytest.raises(InvalidToken):
        await service.verify(f"{header}.{altered}.{signature}")


async def test_ac05_an_unsigned_alg_none_token_is_rejected() -> None:
    claims = {"sub": str(uuid4()), "iat": int(NOW.timestamp()), "exp": int(NOW.timestamp()) + 1800}
    unsigned = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(claims)}."

    with pytest.raises(InvalidToken):
        await make_service(FixedClock(NOW)).verify(unsigned)


@pytest.mark.parametrize(
    "claims",
    [
        {"iat": 0, "exp": 4102444800},
        {"sub": "not-a-uuid", "iat": 0, "exp": 4102444800},
        {"sub": str(uuid4()), "iat": 0},
    ],
)
async def test_ac05_a_correctly_signed_token_with_bad_claims_is_rejected(
    claims: dict[str, object],
) -> None:
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(InvalidToken):
        await make_service(FixedClock(NOW)).verify(token)
