from taskapp.application.ports import TokenService, UnitOfWork
from taskapp.domain.errors import InvalidToken
from taskapp.domain.user import User


class AuthenticateUser:
    def __init__(self, uow: UnitOfWork, tokens: TokenService) -> None:
        self._uow = uow
        self._tokens = tokens

    async def execute(self, token: str) -> User:
        user_id = await self._tokens.verify(token)
        async with self._uow:
            user = await self._uow.users.get(user_id)
        if user is None:
            raise InvalidToken("user no longer exists")
        return user
