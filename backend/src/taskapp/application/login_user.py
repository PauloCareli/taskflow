from taskapp.application.ports import (
    AccessToken,
    Credentials,
    PasswordHasher,
    TokenService,
    UnitOfWork,
)
from taskapp.domain.errors import InvalidCredentials
from taskapp.domain.user import PASSWORD_MAX, is_valid_email, normalize_email


class LoginUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, *, email: str, password: str) -> AccessToken:
        if len(password) > PASSWORD_MAX:
            # No registered user can have this password; do not spend CPU hashing it.
            raise InvalidCredentials("invalid email or password")
        credentials = await self._find(normalize_email(email))
        if credentials is None:
            # Do comparable work so response time does not reveal which emails are registered.
            await self._hasher.hash(password)
            raise InvalidCredentials("invalid email or password")
        if not await self._hasher.verify(password, credentials.password_hash):
            raise InvalidCredentials("invalid email or password")
        return await self._tokens.issue(credentials.user.id)

    async def _find(self, email: str) -> Credentials | None:
        if not is_valid_email(email):
            return None  # can never be registered, and may not be storable or queryable
        async with self._uow:
            return await self._uow.users.get_credentials_by_email(email)
