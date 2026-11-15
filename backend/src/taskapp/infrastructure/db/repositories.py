from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from taskapp.application.ports import Credentials, TaskFilters
from taskapp.domain.task import Task
from taskapp.domain.user import User


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> None:
        raise NotImplementedError

    async def get(self, task_id: UUID) -> Task | None:
        raise NotImplementedError

    async def save(self, task: Task) -> None:
        raise NotImplementedError

    async def delete(self, task_id: UUID) -> None:
        raise NotImplementedError

    async def list_visible(
        self, user_id: UUID, filters: TaskFilters, *, offset: int, limit: int
    ) -> tuple[list[Task], int]:
        raise NotImplementedError


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    async def get_credentials_by_email(self, email: str) -> Credentials | None:
        raise NotImplementedError

    async def add(self, user: User, password_hash: str) -> None:
        raise NotImplementedError
