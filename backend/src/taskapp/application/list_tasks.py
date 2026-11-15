from uuid import UUID

from taskapp.application.ports import Page, TaskFilters, UnitOfWork
from taskapp.domain.errors import ValidationError
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
        if page < 1:
            raise ValidationError("page must be at least 1")
        if not 1 <= size <= MAX_PAGE_SIZE:
            raise ValidationError(f"size must be between 1 and {MAX_PAGE_SIZE}")
        filters = filters or TaskFilters()
        for bound in (filters.due_before, filters.due_after):
            if bound is not None and bound.utcoffset() is None:
                raise ValidationError("due date filters must be timezone-aware")
        async with self._uow:
            items, total = await self._uow.tasks.list_visible(
                actor_id, filters, offset=(page - 1) * size, limit=size
            )
        return Page(items=items, total=total, page=page, size=size)
