from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import UnitOfWork
from taskapp.domain.task import Task


class GetTask:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, actor_id: UUID, task_id: UUID) -> Task:
        async with self._uow:
            return await load_visible_task(self._uow, actor_id, task_id)
