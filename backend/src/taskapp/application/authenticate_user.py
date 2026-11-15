from taskapp.application.ports import TokenService, UnitOfWork
from taskapp.domain.user import User


class AuthenticateUser:
    def __init__(self, uow: UnitOfWork, tokens: TokenService) -> None:
        self._uow = uow
        self._tokens = tokens

    async def execute(self, token: str) -> User:
        raise NotImplementedError
