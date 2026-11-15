from taskapp.application.ports import AccessToken, PasswordHasher, TokenService, UnitOfWork
from taskapp.domain.errors import InvalidCredentials
from taskapp.domain.user import normalize_email


class LoginUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, *, email: str, password: str) -> AccessToken:
        async with self._uow:
            credentials = await self._uow.users.get_credentials_by_email(normalize_email(email))
        if credentials is None:
            # Do comparable work so response time does not reveal which emails are registered.
            await self._hasher.hash(password)
            raise InvalidCredentials("invalid email or password")
        if not await self._hasher.verify(password, credentials.password_hash):
            raise InvalidCredentials("invalid email or password")
        return await self._tokens.issue(credentials.user.id)
