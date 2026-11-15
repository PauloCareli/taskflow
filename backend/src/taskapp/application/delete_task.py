from uuid import UUID

from taskapp.application.ports import UnitOfWork


class DeleteTask:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, actor_id: UUID, task_id: UUID) -> None:
        raise NotImplementedError
