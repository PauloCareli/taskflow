from datetime import datetime
from uuid import UUID

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
        raise NotImplementedError
