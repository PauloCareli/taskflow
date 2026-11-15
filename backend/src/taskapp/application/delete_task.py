from uuid import UUID

from taskapp.application.access import load_visible_task
from taskapp.application.ports import UnitOfWork


class DeleteTask:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, actor_id: UUID, task_id: UUID) -> None:
        async with self._uow:
            task = await load_visible_task(self._uow, actor_id, task_id)
            task.ensure_creator(actor_id)
            await self._uow.tasks.delete(task.id)
            await self._uow.commit()
