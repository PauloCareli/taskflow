from datetime import timedelta
from uuid import uuid4

import pytest

from taskapp.application.change_task_status import ChangeTaskStatus
from taskapp.application.complete_task import CompleteTask
from taskapp.domain.errors import InvalidTransition, TaskNotFound
from taskapp.domain.status import TaskStatus
from taskapp.domain.user import User
from tests.fakes import FixedClock, InMemoryTaskRepository, InMemoryUnitOfWork
from tests.unit.application.helpers import seed_task


async def test_ac05_creator_and_assignee_can_change_the_status(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)
    change = ChangeTaskStatus(uow, clock)

    by_creator = await change.execute(alice.id, task.id, TaskStatus.IN_PROGRESS)
    by_assignee = await change.execute(bob.id, task.id, TaskStatus.BLOCKED)

    assert by_creator.status is TaskStatus.IN_PROGRESS
    assert by_assignee.status is TaskStatus.BLOCKED
    stored = await tasks.get(task.id)
    assert stored is not None
    assert stored.status is TaskStatus.BLOCKED
    assert uow.commits == 2


async def test_ac06_a_user_who_cannot_see_the_task_gets_not_found_for_status_and_complete(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
    carol: User,
) -> None:
    task = await seed_task(tasks, alice.id)

    for task_id, actor in [(task.id, carol.id), (uuid4(), alice.id)]:
        with pytest.raises(TaskNotFound):
            await ChangeTaskStatus(uow, clock).execute(actor, task_id, TaskStatus.BLOCKED)
        with pytest.raises(TaskNotFound):
            await CompleteTask(uow, clock).execute(actor, task_id)

    assert await tasks.get(task.id) == task
    assert uow.commits == 0


async def test_ac03_a_terminal_task_rejects_a_different_status_and_stays_unchanged(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    task = await seed_task(tasks, alice.id, status=TaskStatus.CANCELLED)

    with pytest.raises(InvalidTransition):
        await ChangeTaskStatus(uow, clock).execute(alice.id, task.id, TaskStatus.TODO)

    assert await tasks.get(task.id) == task
    assert uow.commits == 0


async def test_ac03_changing_to_the_current_status_touches_nothing(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    task = await seed_task(tasks, alice.id, status=TaskStatus.COMPLETED)
    clock.set(clock.now() + timedelta(days=1))

    result = await ChangeTaskStatus(uow, clock).execute(alice.id, task.id, TaskStatus.COMPLETED)

    assert result == task
    assert tasks.writes == 0
    assert uow.commits == 0


async def test_ac04_complete_sets_completed_at_from_the_clock(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)
    clock.set(clock.now() + timedelta(hours=3))

    completed = await CompleteTask(uow, clock).execute(bob.id, task.id)

    assert completed.status is TaskStatus.COMPLETED
    assert completed.completed_at == clock.now()
    stored = await tasks.get(task.id)
    assert stored == completed
    assert uow.commits == 1


async def test_ac04_completing_an_already_completed_task_is_a_noop(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
) -> None:
    task = await seed_task(tasks, alice.id, status=TaskStatus.COMPLETED)

    await CompleteTask(uow, clock).execute(alice.id, task.id)

    assert tasks.writes == 0
    assert uow.commits == 0
