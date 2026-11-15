from collections.abc import Collection
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


@dataclass(frozen=True)
class Credentials:
    user: User
    password_hash: str


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_in: int


class UserRepository(Protocol):
    async def get(self, user_id: UUID) -> User | None: ...

    async def get_many(self, user_ids: Collection[UUID]) -> dict[UUID, User]:
        """The users that exist among `user_ids`, in one query."""
        ...

    async def list_all(self) -> list[User]:
        """Every registered user, sorted by name."""
        ...

    async def get_credentials_by_email(self, email: str) -> Credentials | None:
        """Look a user up by normalized email, together with the stored password hash."""
        ...

    async def add(self, user: User, password_hash: str) -> None:
        """Store a user. Raises `EmailTaken` if the email is already registered."""
        ...


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


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...

    async def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(Protocol):
    async def issue(self, user_id: UUID) -> AccessToken: ...

    async def verify(self, token: str) -> UUID:
        """Return the user id in a valid token; raise `InvalidToken` otherwise."""
        ...
