from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import AssignmentMessage, Clock, Notifier, UnitOfWork
from taskapp.domain.errors import UserNotFound
from taskapp.domain.task import Task


class AssignTask:
    def __init__(self, uow: UnitOfWork, clock: Clock, notifier: Notifier) -> None:
        self._uow = uow
        self._clock = clock
        self._notifier = notifier

    async def execute(self, actor_id: UUID, task_id: UUID, assignee_id: UUID | None) -> Task:
        async with self._uow:
            task = await load_visible_task(self._uow, actor_id, task_id)
            task.ensure_creator(actor_id)
            if assignee_id is not None and await self._uow.users.get(assignee_id) is None:
                raise UserNotFound(str(assignee_id))
            if not task.assign(assignee_id, now=self._clock.now()):
                return task
            await self._uow.tasks.save(task)
            await self._uow.commit()
        if assignee_id is not None:
            await self._notifier.notify(AssignmentMessage(task.id, assignee_id))
        return task
