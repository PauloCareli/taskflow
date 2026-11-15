from uuid import UUID

from taskapp.application.ports import Clock, UnitOfWork
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task


class ChangeTaskStatus:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, actor_id: UUID, task_id: UUID, status: TaskStatus) -> Task:
        raise NotImplementedError
