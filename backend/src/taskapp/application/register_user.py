from taskapp.application.ports import PasswordHasher, UnitOfWork
from taskapp.domain.user import User


class RegisterUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher) -> None:
        self._uow = uow
        self._hasher = hasher

    async def execute(self, *, email: str, name: str, password: str) -> User:
        raise NotImplementedError
