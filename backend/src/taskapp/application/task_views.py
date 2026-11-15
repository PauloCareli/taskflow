from collections.abc import Sequence
from dataclasses import dataclass

from taskapp.application.ports import UnitOfWork
from taskapp.domain.task import Task
from taskapp.domain.user import User


@dataclass(frozen=True)
class TaskView:
    """A task together with the people it refers to, ready to be shown."""

    task: Task
    creator: User
    assignee: User | None


class BuildTaskViews:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, tasks: Sequence[Task]) -> list[TaskView]:
        raise NotImplementedError
