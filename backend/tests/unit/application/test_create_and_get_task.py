from datetime import timedelta
from uuid import uuid4

import pytest

from taskapp.application.create_task import CreateTask
from taskapp.application.get_task import GetTask
from taskapp.application.ports import AssignmentMessage
from taskapp.domain.errors import TaskNotFound, UserNotFound, ValidationError
from taskapp.domain.status import TaskStatus
from taskapp.domain.user import User
from tests.fakes import (
    FixedClock,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    RecordingNotifier,
)


def create_use_case(
    uow: InMemoryUnitOfWork, clock: FixedClock, notifier: RecordingNotifier
) -> CreateTask:
    return CreateTask(uow, clock, notifier)


async def test_ac01_create_stores_a_todo_task_owned_by_the_caller(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    due = clock.now() + timedelta(days=2)

    task = await create_use_case(uow, clock, notifier).execute(
        alice.id, title="Write spec", description="details", due_date=due
    )

    stored = await tasks.get(task.id)
    assert stored == task
    assert stored is not None
    assert stored.status is TaskStatus.TODO
    assert stored.creator_id == alice.id
    assert stored.due_date == due
    assert stored.created_at == clock.now()
    assert uow.commits == 1
    assert notifier.messages == []


async def test_ac02_create_with_invalid_input_stores_and_commits_nothing(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    with pytest.raises(ValidationError):
        await create_use_case(uow, clock, notifier).execute(alice.id, title="")
    with pytest.raises(ValidationError):
        await create_use_case(uow, clock, notifier).execute(
            alice.id, title="ok", due_date=clock.now() - timedelta(days=1)
        )

    assert tasks.all() == []
    assert uow.commits == 0


async def test_ac07_create_with_an_assignee_sends_one_message_after_commit(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    alice: User,
    bob: User,
) -> None:
    task = await create_use_case(uow, clock, notifier).execute(
        alice.id, title="Review", assignee_id=bob.id
    )

    assert task.assignee_id == bob.id
    assert notifier.messages == [AssignmentMessage(task_id=task.id, assignee_id=bob.id)]
    assert uow.commits == 1


async def test_ac07_create_with_an_unknown_assignee_fails_and_sends_nothing(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    with pytest.raises(UserNotFound):
        await create_use_case(uow, clock, notifier).execute(
            alice.id, title="Review", assignee_id=uuid4()
        )

    assert tasks.all() == []
    assert notifier.messages == []
    assert uow.commits == 0


async def test_ac06_get_returns_the_task_to_its_creator_and_assignee(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    alice: User,
    bob: User,
) -> None:
    created = await create_use_case(uow, clock, notifier).execute(
        alice.id, title="Review", assignee_id=bob.id
    )

    assert await GetTask(uow).execute(alice.id, created.id) == created
    assert await GetTask(uow).execute(bob.id, created.id) == created


async def test_ac06_get_hides_a_task_from_others_exactly_like_a_missing_one(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    alice: User,
    carol: User,
) -> None:
    created = await create_use_case(uow, clock, notifier).execute(alice.id, title="Private")

    with pytest.raises(TaskNotFound):
        await GetTask(uow).execute(carol.id, created.id)
    with pytest.raises(TaskNotFound):
        await GetTask(uow).execute(alice.id, uuid4())
