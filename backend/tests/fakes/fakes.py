from copy import deepcopy
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from taskapp.application.ports import AssignmentMessage, TaskFilters
from taskapp.domain.task import Task
from taskapp.domain.user import User

_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


class InMemoryTaskRepository:
    """Stores copies, so a change never reaches the "database" without an explicit save."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        self.writes = 0

    async def add(self, task: Task) -> None:
        self.writes += 1
        self._tasks[task.id] = deepcopy(task)

    async def get(self, task_id: UUID) -> Task | None:
        task = self._tasks.get(task_id)
        return deepcopy(task) if task else None

    async def save(self, task: Task) -> None:
        self.writes += 1
        self._tasks[task.id] = deepcopy(task)

    async def delete(self, task_id: UUID) -> None:
        self.writes += 1
        self._tasks.pop(task_id, None)

    async def list_visible(
        self, user_id: UUID, filters: TaskFilters, *, offset: int, limit: int
    ) -> tuple[list[Task], int]:
        matching = [
            t for t in self._tasks.values() if t.is_visible_to(user_id) and _matches(t, filters)
        ]
        matching.sort(key=lambda t: t.created_at, reverse=True)
        matching.sort(key=lambda t: (t.due_date is None, t.due_date or _FAR_FUTURE))
        return [deepcopy(t) for t in matching[offset : offset + limit]], len(matching)

    def all(self) -> list[Task]:
        return [deepcopy(t) for t in self._tasks.values()]


def _matches(task: Task, filters: TaskFilters) -> bool:
    if filters.statuses and task.status not in filters.statuses:
        return False
    if filters.due_before is not None or filters.due_after is not None:
        if task.due_date is None:
            return False
        if filters.due_before is not None and task.due_date > filters.due_before:
            return False
        if filters.due_after is not None and task.due_date < filters.due_after:
            return False
    return True


class InMemoryUserRepository:
    def __init__(self, users: list[User] | None = None) -> None:
        self._users = {u.id: u for u in users or []}

    async def get(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)


class InMemoryUnitOfWork:
    def __init__(self, tasks: InMemoryTaskRepository, users: InMemoryUserRepository) -> None:
        self.tasks = tasks
        self.users = users
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[AssignmentMessage] = []

    async def notify(self, message: AssignmentMessage) -> None:
        self.messages.append(message)
