from taskapp.application.ports import UnitOfWork
from taskapp.domain.user import User


class ListUsers:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self) -> list[User]:
        async with self._uow:
            return await self._uow.users.list_all()
