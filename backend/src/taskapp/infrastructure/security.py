from datetime import UTC, datetime
from uuid import UUID

from taskapp.application.ports import AccessToken, Clock

TOKEN_LIFETIME_SECONDS = 30 * 60


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class Argon2PasswordHasher:
    async def hash(self, password: str) -> str:
        raise NotImplementedError

    async def verify(self, password: str, password_hash: str) -> bool:
        raise NotImplementedError


class JwtTokenService:
    def __init__(
        self, secret: str, clock: Clock, lifetime_seconds: int = TOKEN_LIFETIME_SECONDS
    ) -> None:
        self._secret = secret
        self._clock = clock
        self._lifetime = lifetime_seconds

    async def issue(self, user_id: UUID) -> AccessToken:
        raise NotImplementedError

    async def verify(self, token: str) -> UUID:
        raise NotImplementedError
