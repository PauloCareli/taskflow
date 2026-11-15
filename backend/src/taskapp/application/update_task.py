from datetime import datetime
from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import Clock, UnitOfWork
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import UNSET, Task, Unset


class UpdateTask:
    """Change a task's fields and/or status in one transaction: all of it or none of it.

    Fields (title, description, due date) are for the creator; the status can also be changed
    by the assignee. Asking for nothing, or for the status the task already has, is a no-op.
    """

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        actor_id: UUID,
        task_id: UUID,
        *,
        title: str | Unset = UNSET,
        description: str | Unset | None = UNSET,
        due_date: datetime | Unset | None = UNSET,
        status: TaskStatus | None = None,
    ) -> Task:
        edits_fields = any(not isinstance(v, Unset) for v in (title, description, due_date))
        async with self._uow:
            task = await load_visible_task(self._uow, actor_id, task_id)
            if edits_fields:
                task.ensure_creator(actor_id)
            if status is not None:
                task.ensure_can_change_status(actor_id)
            now = self._clock.now()
            if edits_fields:
                task.update(now=now, title=title, description=description, due_date=due_date)
            status_changed = status is not None and task.change_status(status, now=now)
            if edits_fields or status_changed:
                await self._uow.tasks.save(task)
                await self._uow.commit()
        return task
