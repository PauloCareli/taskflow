from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from taskapp.domain.status import TaskStatus

TITLE_MAX = 120
DESCRIPTION_MAX = 2000


class _Unset:
    """Marks a field the caller did not provide, so None can mean "clear it"."""


UNSET = _Unset()


@dataclass
class Task:
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: datetime | None
    creator_id: UUID
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        title: str,
        description: str | None,
        due_date: datetime | None,
        creator_id: UUID,
        assignee_id: UUID | None,
        now: datetime,
    ) -> "Task":
        raise NotImplementedError

    def update(
        self,
        *,
        now: datetime,
        title: str | _Unset = UNSET,
        description: str | _Unset | None = UNSET,
        due_date: datetime | _Unset | None = UNSET,
    ) -> None:
        raise NotImplementedError

    def change_status(self, new_status: TaskStatus, *, now: datetime) -> bool:
        raise NotImplementedError

    def assign(self, assignee_id: UUID | None, *, now: datetime) -> bool:
        raise NotImplementedError

    def is_visible_to(self, user_id: UUID) -> bool:
        raise NotImplementedError

    def ensure_creator(self, user_id: UUID) -> None:
        raise NotImplementedError

    def ensure_can_change_status(self, user_id: UUID) -> None:
        raise NotImplementedError
