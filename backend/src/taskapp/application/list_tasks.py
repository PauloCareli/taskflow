from uuid import UUID

from taskapp.application.ports import Page, TaskFilters, UnitOfWork
from taskapp.domain.task import Task

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class ListTasks:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        actor_id: UUID,
        filters: TaskFilters | None = None,
        *,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> Page[Task]:
        raise NotImplementedError
