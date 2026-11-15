from datetime import timedelta
from uuid import uuid4

import pytest

from taskapp.application.assign_task import AssignTask
from taskapp.application.ports import AssignmentMessage
from taskapp.domain.errors import PermissionDenied, TaskNotFound, UserNotFound
from taskapp.domain.user import User
from tests.fakes import (
    FixedClock,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    RecordingNotifier,
)
from tests.unit.application.helpers import seed_task


async def test_ac07_assigning_saves_the_assignee_and_sends_one_message_after_commit(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id)
    clock.set(clock.now() + timedelta(hours=1))

    assigned = await AssignTask(uow, clock, notifier).execute(alice.id, task.id, bob.id)

    stored = await tasks.get(task.id)
    assert stored == assigned
    assert stored is not None
    assert stored.assignee_id == bob.id
    assert stored.updated_at == clock.now()
    assert notifier.messages == [AssignmentMessage(task_id=task.id, assignee_id=bob.id)]
    assert uow.commits == 1


async def test_ac07_the_creator_can_assign_to_themselves(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    task = await seed_task(tasks, alice.id)

    assigned = await AssignTask(uow, clock, notifier).execute(alice.id, task.id, alice.id)

    assert assigned.assignee_id == alice.id
    assert len(notifier.messages) == 1


async def test_ac07_reassigning_messages_only_the_new_assignee(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
    carol: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)

    await AssignTask(uow, clock, notifier).execute(alice.id, task.id, carol.id)

    assert notifier.messages == [AssignmentMessage(task_id=task.id, assignee_id=carol.id)]


async def test_ac07_assigning_the_current_assignee_is_a_noop(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)
    clock.set(clock.now() + timedelta(days=1))

    result = await AssignTask(uow, clock, notifier).execute(alice.id, task.id, bob.id)

    assert result == task
    assert tasks.writes == 0
    assert uow.commits == 0
    assert notifier.messages == []


async def test_ac07_unassigning_clears_the_assignee_without_a_message(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)

    result = await AssignTask(uow, clock, notifier).execute(alice.id, task.id, None)

    assert result.assignee_id is None
    assert uow.commits == 1
    assert notifier.messages == []


async def test_ac07_assigning_an_unknown_user_changes_and_sends_nothing(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    task = await seed_task(tasks, alice.id)

    with pytest.raises(UserNotFound):
        await AssignTask(uow, clock, notifier).execute(alice.id, task.id, uuid4())

    assert await tasks.get(task.id) == task
    assert uow.commits == 0
    assert notifier.messages == []


async def test_ac05_only_the_creator_can_assign(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
    carol: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)

    with pytest.raises(PermissionDenied):
        await AssignTask(uow, clock, notifier).execute(bob.id, task.id, carol.id)

    assert await tasks.get(task.id) == task
    assert notifier.messages == []


async def test_ac06_assigning_a_task_the_caller_cannot_see_is_not_found(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    notifier: RecordingNotifier,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
    carol: User,
) -> None:
    task = await seed_task(tasks, alice.id)

    for task_id, actor in [(task.id, carol.id), (uuid4(), alice.id)]:
        with pytest.raises(TaskNotFound):
            await AssignTask(uow, clock, notifier).execute(actor, task_id, bob.id)

    assert notifier.messages == []
    assert uow.commits == 0
