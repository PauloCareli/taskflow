from datetime import datetime
from uuid import UUID

from taskapp.application.ports import Clock, Notifier, UnitOfWork
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
        raise NotImplementedError
