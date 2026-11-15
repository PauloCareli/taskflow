from datetime import datetime
from uuid import UUID

from taskapp.application.ports import AssignmentMessage, Clock, Notifier, UnitOfWork
from taskapp.domain.errors import UserNotFound
from taskapp.domain.task import Task


class CreateTask:
    def __init__(self, uow: UnitOfWork, clock: Clock, notifier: Notifier) -> None:
        self._uow = uow
        self._clock = clock
        self._notifier = notifier

    async def execute(
        self,
        actor_id: UUID,
        *,
        title: str,
        description: str | None = None,
        due_date: datetime | None = None,
        assignee_id: UUID | None = None,
    ) -> Task:
        async with self._uow:
            task = Task.create(
                title=title,
                description=description,
                due_date=due_date,
                creator_id=actor_id,
                assignee_id=assignee_id,
                now=self._clock.now(),
            )
            if assignee_id is not None and await self._uow.users.get(assignee_id) is None:
                raise UserNotFound(str(assignee_id))
            await self._uow.tasks.add(task)
            await self._uow.commit()
        if assignee_id is not None:
            await self._notifier.notify(AssignmentMessage(task.id, assignee_id))
        return task
