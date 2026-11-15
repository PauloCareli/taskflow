from taskapp.application.ports import AccessToken, PasswordHasher, TokenService, UnitOfWork


class LoginUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, *, email: str, password: str) -> AccessToken:
        raise NotImplementedError
