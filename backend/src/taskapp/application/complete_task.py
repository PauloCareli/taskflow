from uuid import UUID

from taskapp.application.change_task_status import ChangeTaskStatus
from taskapp.application.ports import Clock, UnitOfWork
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task


class CompleteTask:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._change_status = ChangeTaskStatus(uow, clock)

    async def execute(self, actor_id: UUID, task_id: UUID) -> Task:
        return await self._change_status.execute(actor_id, task_id, TaskStatus.COMPLETED)
