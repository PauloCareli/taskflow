import asyncio
from datetime import UTC, datetime
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from taskapp.application.ports import AccessToken, Clock
from taskapp.domain.errors import InvalidToken

TOKEN_LIFETIME_SECONDS = 30 * 60
_ALGORITHM = "HS256"


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class Argon2PasswordHasher:
    """argon2 through pwdlib; the CPU-bound work runs in a thread, off the event loop."""

    def __init__(self) -> None:
        self._hash = PasswordHash((Argon2Hasher(),))

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._hash.verify, password, password_hash)


class JwtTokenService:
    def __init__(
        self, secret: str, clock: Clock, lifetime_seconds: int = TOKEN_LIFETIME_SECONDS
    ) -> None:
        self._secret = secret
        self._clock = clock
        self._lifetime = lifetime_seconds

    async def issue(self, user_id: UUID) -> AccessToken:
        issued_at = int(self._clock.now().timestamp())
        claims = {"sub": str(user_id), "iat": issued_at, "exp": issued_at + self._lifetime}
        token = jwt.encode(claims, self._secret, algorithm=_ALGORITHM)
        return AccessToken(token=token, expires_in=self._lifetime)

    async def verify(self, token: str) -> UUID:
        try:
            # Expiry is checked against the injected clock below, not the system clock.
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                options={
                    "require": ["sub", "iat", "exp"],
                    "verify_exp": False,
                    "verify_iat": False,
                },
            )
            if int(claims["exp"]) <= int(self._clock.now().timestamp()):
                raise InvalidToken("token expired")
            return UUID(str(claims["sub"]))
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise InvalidToken("token is not valid") from error
