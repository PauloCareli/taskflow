from dataclasses import dataclass, field
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task
from taskapp.domain.user import User


@dataclass(frozen=True)
class TaskFilters:
    """Listing filters. New filters are added here, not as per-endpoint parameters."""

    statuses: frozenset[TaskStatus] = field(default_factory=frozenset)
    due_before: datetime | None = None
    due_after: datetime | None = None


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    size: int


@dataclass(frozen=True)
class AssignmentMessage:
    task_id: UUID
    assignee_id: UUID


class TaskRepository(Protocol):
    async def add(self, task: Task) -> None: ...

    async def get(self, task_id: UUID) -> Task | None: ...

    async def save(self, task: Task) -> None: ...

    async def delete(self, task_id: UUID) -> None: ...

    async def list_visible(
        self, user_id: UUID, filters: TaskFilters, *, offset: int, limit: int
    ) -> tuple[list[Task], int]:
        """Tasks the user created or is assigned to, filtered and sorted by due date
        ascending (no due date last) then creation time descending, plus the total count."""
        ...


class UserRepository(Protocol):
    async def get(self, user_id: UUID) -> User | None: ...


class UnitOfWork(Protocol):
    @property
    def tasks(self) -> TaskRepository: ...

    @property
    def users(self) -> UserRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class Notifier(Protocol):
    async def notify(self, message: AssignmentMessage) -> None: ...
