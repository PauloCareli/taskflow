from collections.abc import Sequence
from dataclasses import dataclass

from taskapp.application.ports import UnitOfWork
from taskapp.domain.errors import UserNotFound
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
        if not tasks:
            return []
        wanted = {t.creator_id for t in tasks} | {t.assignee_id for t in tasks if t.assignee_id}
        async with self._uow:
            users = await self._uow.users.get_many(wanted)  # one query for all tasks
        try:
            return [
                TaskView(
                    task=task,
                    creator=users[task.creator_id],
                    assignee=users[task.assignee_id] if task.assignee_id else None,
                )
                for task in tasks
            ]
        except KeyError as error:
            raise UserNotFound(str(error.args[0])) from error
