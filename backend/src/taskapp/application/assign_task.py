from uuid import UUID

from taskapp.application.ports import Clock, Notifier, UnitOfWork
from taskapp.domain.task import Task


class AssignTask:
    def __init__(self, uow: UnitOfWork, clock: Clock, notifier: Notifier) -> None:
        self._uow = uow
        self._clock = clock
        self._notifier = notifier

    async def execute(self, actor_id: UUID, task_id: UUID, assignee_id: UUID | None) -> Task:
        raise NotImplementedError
