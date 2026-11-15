from uuid import UUID

from taskapp.application.ports import Page, TaskFilters, UnitOfWork
from taskapp.domain.errors import ValidationError
from taskapp.domain.task import Task
from taskapp.domain.times import check_aware

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
        if page < 1:
            raise ValidationError("page must be at least 1")
        if not 1 <= size <= MAX_PAGE_SIZE:
            raise ValidationError(f"size must be at least 1; the maximum size is {MAX_PAGE_SIZE}")
        filters = filters or TaskFilters()
        check_aware(filters.due_before, "due_before")
        check_aware(filters.due_after, "due_after")
        async with self._uow:
            items, total = await self._uow.tasks.list_visible(
                actor_id, filters, offset=(page - 1) * size, limit=size
            )
        return Page(items=items, total=total, page=page, size=size)
