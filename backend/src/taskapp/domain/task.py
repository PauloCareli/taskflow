from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from taskapp.domain.errors import InvalidTransition, PermissionDenied, ValidationError
from taskapp.domain.status import TERMINAL_STATUSES, TaskStatus
from taskapp.domain.times import check_aware

TITLE_MAX = 120
DESCRIPTION_MAX = 2000


class Unset:
    """Marks a field the caller did not provide, so None can mean "clear it"."""


UNSET = Unset()


def _check_title(title: str) -> None:
    if not 1 <= len(title) <= TITLE_MAX:
        raise ValidationError(f"title must be 1-{TITLE_MAX} characters")


def _check_description(description: str | None) -> None:
    if description is not None and len(description) > DESCRIPTION_MAX:
        raise ValidationError(f"description must be at most {DESCRIPTION_MAX} characters")


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
        _check_title(title)
        _check_description(description)
        check_aware(due_date, "due_date")
        if due_date is not None and due_date < now:
            raise ValidationError("due_date must not be in the past")
        return cls(
            id=uuid4(),
            title=title,
            description=description,
            status=TaskStatus.TODO,
            due_date=due_date,
            creator_id=creator_id,
            assignee_id=assignee_id,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

    def update(
        self,
        *,
        now: datetime,
        title: str | Unset = UNSET,
        description: str | Unset | None = UNSET,
        due_date: datetime | Unset | None = UNSET,
    ) -> None:
        if not isinstance(title, Unset):
            _check_title(title)
        if not isinstance(description, Unset):
            _check_description(description)
        if not isinstance(due_date, Unset):
            check_aware(due_date, "due_date")
        if not isinstance(title, Unset):
            self.title = title
        if not isinstance(description, Unset):
            self.description = description
        if not isinstance(due_date, Unset):
            self.due_date = due_date
        self.updated_at = now

    def change_status(self, new_status: TaskStatus, *, now: datetime) -> bool:
        """Move to `new_status`. Returns False (and changes nothing) if already there."""
        if new_status == self.status:
            return False
        if self.status in TERMINAL_STATUSES:
            raise InvalidTransition(f"cannot change a {self.status} task to {new_status}")
        self.status = new_status
        self.completed_at = now if new_status is TaskStatus.COMPLETED else None
        self.updated_at = now
        return True

    def assign(self, assignee_id: UUID | None, *, now: datetime) -> bool:
        """Set the assignee. Returns False (and changes nothing) if it is already that user."""
        if assignee_id == self.assignee_id:
            return False
        self.assignee_id = assignee_id
        self.updated_at = now
        return True

    def is_visible_to(self, user_id: UUID) -> bool:
        return user_id in (self.creator_id, self.assignee_id)

    def ensure_creator(self, user_id: UUID) -> None:
        if user_id != self.creator_id:
            raise PermissionDenied("only the creator can do this")

    def ensure_can_change_status(self, user_id: UUID) -> None:
        if not self.is_visible_to(user_id):
            raise PermissionDenied("only the creator or the assignee can change the status")
