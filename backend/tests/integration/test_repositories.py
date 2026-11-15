import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from taskapp.application.ports import TaskFilters
from taskapp.application.register_user import RegisterUser
from taskapp.domain.errors import EmailTaken
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task
from taskapp.domain.user import User
from taskapp.infrastructure.db.unit_of_work import SqlUnitOfWork
from tests.fakes import FakePasswordHasher

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)

Factory = async_sessionmaker[AsyncSession]


async def add_users(factory: Factory, *emails: str) -> list[User]:
    users = [User.create(email=email, name=email.split("@")[0]) for email in emails]
    uow = SqlUnitOfWork(factory)
    async with uow:
        for user in users:
            await uow.users.add(user, f"hash-of-{user.name}")
        await uow.commit()
    return users


def build_task(
    creator: UUID,
    title: str = "Task",
    *,
    assignee: UUID | None = None,
    due_date: datetime | None = None,
    status: TaskStatus = TaskStatus.TODO,
    created_at: datetime = NOW,
) -> Task:
    task = Task.create(
        title=title,
        description=None,
        due_date=due_date,
        creator_id=creator,
        assignee_id=assignee,
        now=created_at,
    )
    task.status = status
    return task


async def store(factory: Factory, *tasks: Task) -> None:
    uow = SqlUnitOfWork(factory)
    async with uow:
        for task in tasks:
            await uow.tasks.add(task)
        await uow.commit()


async def fetch(factory: Factory, task_id: UUID) -> Task | None:
    async with SqlUnitOfWork(factory) as uow:
        return await uow.tasks.get(task_id)


async def list_titles(
    factory: Factory,
    user: UUID,
    filters: TaskFilters | None = None,
    *,
    offset: int = 0,
    limit: int = 25,
) -> list[str]:
    async with SqlUnitOfWork(factory) as uow:
        items, _ = await uow.tasks.list_visible(
            user, filters or TaskFilters(), offset=offset, limit=limit
        )
    return [t.title for t in items]


async def test_ac06_a_task_is_stored_and_read_back_unchanged(
    session_factory: Factory,
) -> None:
    (alice, bob) = await add_users(session_factory, "alice@example.com", "bob@example.com")
    task = Task.create(
        title="Write spec",
        description="details",
        due_date=NOW + timedelta(days=2),
        creator_id=alice.id,
        assignee_id=bob.id,
        now=NOW,
    )

    await store(session_factory, task)

    assert await fetch(session_factory, task.id) == task


async def test_ac06_saving_and_deleting_a_task(session_factory: Factory) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")
    task = build_task(alice.id)
    await store(session_factory, task)

    task.update(now=NOW + timedelta(hours=1), title="Renamed", description="more")
    task.change_status(TaskStatus.COMPLETED, now=NOW + timedelta(hours=2))
    async with SqlUnitOfWork(session_factory) as uow:
        await uow.tasks.save(task)
        await uow.commit()
    assert await fetch(session_factory, task.id) == task

    async with SqlUnitOfWork(session_factory) as uow:
        await uow.tasks.delete(task.id)
        await uow.commit()
    assert await fetch(session_factory, task.id) is None


async def test_ac06_work_that_is_not_committed_or_that_fails_is_not_stored(
    session_factory: Factory,
) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")
    forgotten = build_task(alice.id, "never committed")
    failed = build_task(alice.id, "rolled back")

    async with SqlUnitOfWork(session_factory) as uow:
        await uow.tasks.add(forgotten)
    with pytest.raises(RuntimeError):
        async with SqlUnitOfWork(session_factory) as uow:
            await uow.tasks.add(failed)
            await uow.commit()
            raise RuntimeError("boom after commit does not undo it")

    assert await fetch(session_factory, forgotten.id) is None
    assert await fetch(session_factory, failed.id) == failed


async def test_ac06_users_are_stored_with_their_hash_and_found_by_email(
    session_factory: Factory,
) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")

    async with SqlUnitOfWork(session_factory) as uow:
        credentials = await uow.users.get_credentials_by_email("alice@example.com")
        by_id = await uow.users.get(alice.id)
        missing = await uow.users.get_credentials_by_email("nobody@example.com")

    assert credentials is not None
    assert credentials.user == alice
    assert credentials.password_hash == "hash-of-alice"
    assert by_id == alice
    assert missing is None


async def test_ac06_adding_a_user_with_a_taken_email_in_any_case_raises_email_taken(
    session_factory: Factory,
) -> None:
    await add_users(session_factory, "alice@example.com")
    clone = User(id=UUID(int=1), email="ALICE@example.com", name="Clone")

    with pytest.raises(EmailTaken):
        async with SqlUnitOfWork(session_factory) as uow:
            await uow.users.add(clone, "hash")
            await uow.commit()


async def test_ac06_concurrent_registrations_of_one_email_store_one_user(
    session_factory: Factory,
) -> None:
    hasher = FakePasswordHasher()

    async def register(name: str) -> object:
        try:
            return await RegisterUser(SqlUnitOfWork(session_factory), hasher).execute(
                email="race@example.com", name=name, password="s3cret-pass"
            )
        except EmailTaken as error:
            return error

    results = await asyncio.gather(*(register(f"user{i}") for i in range(5)))

    assert sum(isinstance(r, User) for r in results) == 1
    assert sum(isinstance(r, EmailTaken) for r in results) == 4


async def test_ac06_listing_returns_only_tasks_the_user_created_or_is_assigned_to(
    session_factory: Factory,
) -> None:
    alice, bob, carol = await add_users(
        session_factory, "alice@example.com", "bob@example.com", "carol@example.com"
    )
    await store(
        session_factory,
        build_task(alice.id, "mine"),
        build_task(bob.id, "assigned to me", assignee=alice.id),
        build_task(bob.id, "not mine"),
        build_task(carol.id, "also not mine", assignee=bob.id),
    )

    assert sorted(await list_titles(session_factory, alice.id)) == ["assigned to me", "mine"]


async def test_ac06_listing_filters_by_status_and_inclusive_due_bounds(
    session_factory: Factory,
) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")
    tasks = [build_task(alice.id, f"d{d}", due_date=NOW + timedelta(days=d)) for d in (1, 2, 3, 4)]
    tasks.append(build_task(alice.id, "no due date"))
    tasks.append(build_task(alice.id, "done", status=TaskStatus.COMPLETED))
    await store(session_factory, *tasks)

    statuses = TaskFilters(statuses=frozenset({TaskStatus.COMPLETED}))
    window = TaskFilters(due_after=NOW + timedelta(days=2), due_before=NOW + timedelta(days=3))
    combined = TaskFilters(
        statuses=frozenset({TaskStatus.TODO}), due_before=NOW + timedelta(days=1)
    )

    assert await list_titles(session_factory, alice.id, statuses) == ["done"]
    assert await list_titles(session_factory, alice.id, window) == ["d2", "d3"]
    assert await list_titles(session_factory, alice.id, combined) == ["d1"]


async def test_ac06_listing_sorts_by_due_date_then_newest_first_with_no_due_date_last(
    session_factory: Factory,
) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")
    later = NOW + timedelta(hours=1)
    await store(
        session_factory,
        build_task(alice.id, "no due, old"),
        build_task(alice.id, "no due, new", created_at=NOW + timedelta(hours=2)),
        build_task(alice.id, "later", due_date=NOW + timedelta(days=5)),
        build_task(alice.id, "soon, old", due_date=NOW + timedelta(days=1)),
        build_task(alice.id, "soon, new", due_date=NOW + timedelta(days=1), created_at=later),
    )

    assert await list_titles(session_factory, alice.id) == [
        "soon, new",
        "soon, old",
        "later",
        "no due, new",
        "no due, old",
    ]


async def test_ac06_pages_do_not_overlap_and_total_counts_all_matches(
    session_factory: Factory,
) -> None:
    (alice,) = await add_users(session_factory, "alice@example.com")
    await store(
        session_factory,
        *(build_task(alice.id, f"t{i}", created_at=NOW + timedelta(minutes=i)) for i in range(5)),
    )

    pages = [await list_titles(session_factory, alice.id, offset=o, limit=2) for o in (0, 2, 4, 6)]
    async with SqlUnitOfWork(session_factory) as uow:
        _, total = await uow.tasks.list_visible(alice.id, TaskFilters(), offset=6, limit=2)

    assert pages == [["t4", "t3"], ["t2", "t1"], ["t0"], []]
    assert total == 5


async def test_ac06_listing_runs_the_same_number_of_statements_whatever_the_page_size(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    alice, bob = await add_users(session_factory, "alice@example.com", "bob@example.com")
    await store(
        session_factory,
        *(build_task(alice.id, f"t{i}", assignee=bob.id) for i in range(40)),
    )
    statements: list[str] = []

    def record(
        conn: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    await list_titles(session_factory, alice.id, limit=2)
    small = len(statements)
    statements.clear()
    await list_titles(session_factory, alice.id, limit=40)

    assert small == len(statements)
    assert small <= 3


async def test_ac04_get_many_returns_the_users_that_exist_in_one_query(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    alice, bob = await add_users(session_factory, "alice@example.com", "bob@example.com")
    statements: list[str] = []

    def record(
        conn: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    async with SqlUnitOfWork(session_factory) as uow:
        found = await uow.users.get_many({alice.id, bob.id, UUID(int=7)})
        nothing = await uow.users.get_many(set())

    assert found == {alice.id: alice, bob.id: bob}
    assert nothing == {}
    assert len(statements) == 1


async def test_ac08_list_all_returns_every_user_sorted_by_name_ignoring_case(
    session_factory: Factory,
) -> None:
    users = [
        User.create(email="z@example.com", name="zoe"),
        User.create(email="a@example.com", name="Bruno"),
        User.create(email="m@example.com", name="alice"),
    ]
    uow = SqlUnitOfWork(session_factory)
    async with uow:
        for user in users:
            await uow.users.add(user, "hash")
        await uow.commit()

    async with SqlUnitOfWork(session_factory) as reader:
        listed = await reader.users.list_all()

    assert [u.name for u in listed] == ["alice", "Bruno", "zoe"]
