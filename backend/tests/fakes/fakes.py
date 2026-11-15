from copy import deepcopy
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from taskapp.application.ports import (
    AccessToken,
    AssignmentMessage,
    Credentials,
    TaskFilters,
)
from taskapp.domain.errors import EmailTaken, InvalidToken
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
        self._hashes: dict[UUID, str] = {}

    async def get(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    async def get_credentials_by_email(self, email: str) -> Credentials | None:
        for user in self._users.values():
            if user.email == email and user.id in self._hashes:
                return Credentials(user, self._hashes[user.id])
        return None

    async def add(self, user: User, password_hash: str) -> None:
        if any(u.email == user.email for u in self._users.values()):
            raise EmailTaken(user.email)
        self._users[user.id] = user
        self._hashes[user.id] = password_hash

    def remove(self, user_id: UUID) -> None:
        self._users.pop(user_id, None)

    def all(self) -> list[User]:
        return list(self._users.values())

    def stored_hash(self, user_id: UUID) -> str | None:
        return self._hashes.get(user_id)


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


class FakePasswordHasher:
    """Reversible stand-in for argon2; counts calls so tests can see work being done."""

    def __init__(self) -> None:
        self.hash_calls = 0
        self.verify_calls = 0

    async def hash(self, password: str) -> str:
        self.hash_calls += 1
        return f"hashed:{password}"

    async def verify(self, password: str, password_hash: str) -> bool:
        self.verify_calls += 1
        return password_hash == f"hashed:{password}"


class FakeTokenService:
    def __init__(self) -> None:
        self._tokens: dict[str, UUID] = {}

    async def issue(self, user_id: UUID) -> AccessToken:
        token = f"token-{len(self._tokens)}"
        self._tokens[token] = user_id
        return AccessToken(token=token, expires_in=1800)

    async def verify(self, token: str) -> UUID:
        try:
            return self._tokens[token]
        except KeyError:
            raise InvalidToken from None
