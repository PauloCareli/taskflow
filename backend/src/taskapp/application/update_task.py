from datetime import datetime
from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import Clock, UnitOfWork
from taskapp.domain.task import UNSET, Task, Unset


class UpdateTask:
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
    ) -> Task:
        async with self._uow:
            task = await load_visible_task(self._uow, actor_id, task_id)
            task.ensure_creator(actor_id)
            task.update(
                now=self._clock.now(), title=title, description=description, due_date=due_date
            )
            await self._uow.tasks.save(task)
            await self._uow.commit()
        return task
