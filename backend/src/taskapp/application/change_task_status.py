from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import Clock, UnitOfWork
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task


class ChangeTaskStatus:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, actor_id: UUID, task_id: UUID, status: TaskStatus) -> Task:
        async with self._uow:
            task = await load_visible_task(self._uow, actor_id, task_id)
            task.ensure_can_change_status(actor_id)
            if task.change_status(status, now=self._clock.now()):
                await self._uow.tasks.save(task)
                await self._uow.commit()
        return task
