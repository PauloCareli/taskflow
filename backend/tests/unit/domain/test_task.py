from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from taskapp.domain.errors import InvalidTransition, PermissionDenied, ValidationError
from taskapp.domain.status import TERMINAL_STATUSES, TaskStatus
from taskapp.domain.task import Task

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
CREATOR = uuid4()
ASSIGNEE = uuid4()
OTHER = uuid4()

OPEN_STATUSES = [s for s in TaskStatus if s not in TERMINAL_STATUSES]


def make_task(
    *,
    title: str = "Write spec",
    description: str | None = None,
    due_date: datetime | None = None,
    assigned: bool = False,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    task = Task.create(
        title=title,
        description=description,
        due_date=due_date,
        creator_id=CREATOR,
        assignee_id=ASSIGNEE if assigned else None,
        now=NOW,
    )
    task.status = status
    return task


def test_ac01_new_task_defaults_to_todo_with_creator_and_clock_timestamps() -> None:
    due = NOW + timedelta(days=1)

    task = Task.create(
        title="Write spec",
        description="details",
        due_date=due,
        creator_id=CREATOR,
        assignee_id=ASSIGNEE,
        now=NOW,
    )

    assert task.status is TaskStatus.TODO
    assert task.creator_id == CREATOR
    assert task.assignee_id == ASSIGNEE
    assert task.description == "details"
    assert task.due_date == due
    assert task.completed_at is None
    assert task.created_at == NOW
    assert task.updated_at == NOW


@pytest.mark.parametrize("length", [1, 120])
def test_ac02_title_lengths_within_bounds_are_accepted(length: int) -> None:
    assert len(make_task(title="a" * length).title) == length


@pytest.mark.parametrize("length", [0, 121])
def test_ac02_title_lengths_outside_bounds_are_rejected(length: int) -> None:
    with pytest.raises(ValidationError):
        make_task(title="a" * length)


def test_ac02_description_of_2000_characters_is_accepted() -> None:
    assert make_task(description="a" * 2000).description == "a" * 2000


def test_ac02_description_of_2001_characters_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_task(description="a" * 2001)


def test_ac02_update_validates_title_and_description() -> None:
    task = make_task()

    with pytest.raises(ValidationError):
        task.update(now=LATER, title="")
    with pytest.raises(ValidationError):
        task.update(now=LATER, description="a" * 2001)

    assert task.title == "Write spec"
    assert task.updated_at == NOW


def test_ac02_update_changes_only_the_given_fields_and_can_clear_them() -> None:
    task = make_task(description="old", due_date=NOW + timedelta(days=1))

    task.update(now=LATER, title="New title")
    assert (task.title, task.description) == ("New title", "old")
    assert task.due_date is not None

    task.update(now=LATER, description=None, due_date=None)
    assert task.description is None
    assert task.due_date is None
    assert task.updated_at == LATER


def test_ac02_due_date_in_the_past_is_rejected_on_create() -> None:
    with pytest.raises(ValidationError):
        make_task(due_date=NOW - timedelta(seconds=1))


def test_ac02_due_date_equal_to_now_is_accepted_on_create() -> None:
    assert make_task(due_date=NOW).due_date == NOW


def test_ac02_due_date_in_the_past_is_accepted_on_update() -> None:
    task = make_task()

    task.update(now=LATER, due_date=NOW - timedelta(days=3))

    assert task.due_date == NOW - timedelta(days=3)


def test_ac02_naive_datetimes_are_rejected() -> None:
    naive = datetime(2026, 2, 1, 12, 0)
    with pytest.raises(ValidationError):
        make_task(due_date=naive)
    task = make_task()
    with pytest.raises(ValidationError):
        task.update(now=LATER, due_date=naive)


@pytest.mark.parametrize("source", OPEN_STATUSES)
@pytest.mark.parametrize("target", list(TaskStatus))
def test_ac03_open_statuses_may_move_to_any_other_status(
    source: TaskStatus, target: TaskStatus
) -> None:
    task = make_task(status=source)

    changed = task.change_status(target, now=LATER)

    assert changed is (target != source)
    assert task.status is target


TERMINAL_TO_DIFFERENT = [
    (source, target)
    for source in sorted(TERMINAL_STATUSES)
    for target in TaskStatus
    if target != source
]


@pytest.mark.parametrize(("source", "target"), TERMINAL_TO_DIFFERENT)
def test_ac03_terminal_statuses_cannot_change_to_a_different_status(
    source: TaskStatus, target: TaskStatus
) -> None:
    task = make_task(status=source)

    with pytest.raises(InvalidTransition):
        task.change_status(target, now=LATER)

    assert task.status is source
    assert task.updated_at == NOW


@pytest.mark.parametrize("status", list(TaskStatus))
def test_ac03_changing_to_the_current_status_is_a_noop(status: TaskStatus) -> None:
    task = make_task(status=status)

    changed = task.change_status(status, now=LATER)

    assert changed is False
    assert task.updated_at == NOW


def test_ac04_completed_at_is_set_from_the_clock_on_completion() -> None:
    task = make_task()

    task.change_status(TaskStatus.COMPLETED, now=LATER)

    assert task.completed_at == LATER
    assert task.updated_at == LATER


@pytest.mark.parametrize(
    "target", [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELLED]
)
def test_ac04_completed_at_stays_empty_for_other_statuses(target: TaskStatus) -> None:
    task = make_task()

    task.change_status(target, now=LATER)

    assert task.completed_at is None


def test_ac05_only_the_creator_passes_the_creator_check() -> None:
    task = make_task(assigned=True)

    task.ensure_creator(CREATOR)
    for user in (ASSIGNEE, OTHER):
        with pytest.raises(PermissionDenied):
            task.ensure_creator(user)


def test_ac05_creator_and_assignee_may_change_status_others_may_not() -> None:
    task = make_task(assigned=True)

    task.ensure_can_change_status(CREATOR)
    task.ensure_can_change_status(ASSIGNEE)
    with pytest.raises(PermissionDenied):
        task.ensure_can_change_status(OTHER)


def test_ac06_task_is_visible_only_to_creator_and_assignee() -> None:
    task = make_task(assigned=True)

    assert task.is_visible_to(CREATOR)
    assert task.is_visible_to(ASSIGNEE)
    assert not task.is_visible_to(OTHER)


def test_ac07_assign_sets_changes_and_clears_the_assignee() -> None:
    task = make_task()

    assert task.assign(ASSIGNEE, now=LATER) is True
    assert task.assignee_id == ASSIGNEE
    assert task.updated_at == LATER

    assert task.assign(ASSIGNEE, now=LATER + timedelta(hours=1)) is False
    assert task.updated_at == LATER

    assert task.assign(None, now=LATER + timedelta(hours=2)) is True
    assert task.assignee_id is None
