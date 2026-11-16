"""Seed command: `python -m taskapp.seed` (see `just seed`).

Loads three demo users and a set of tasks through the same use cases the API uses. Part of the
composition root, so it may use `infrastructure` directly.
"""

import asyncio
import sys
from collections.abc import Callable
from datetime import timedelta
from enum import StrEnum
from uuid import UUID

from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import AsyncEngine

from taskapp.application.create_task import CreateTask
from taskapp.application.ports import AssignmentMessage
from taskapp.application.register_user import RegisterUser
from taskapp.application.update_task import UpdateTask
from taskapp.domain.status import TaskStatus
from taskapp.domain.user import User
from taskapp.infrastructure.db.models import TaskModel, UserModel
from taskapp.infrastructure.db.session import create_engine, create_session_factory
from taskapp.infrastructure.db.unit_of_work import SqlUnitOfWork
from taskapp.infrastructure.security import Argon2PasswordHasher, SystemClock
from taskapp.infrastructure.settings import LOCAL_ENVIRONMENTS, DatabaseSettings

DEMO_PASSWORD = "password123"  # noqa: S105 (documented demo credential, not a secret)
DEMO_USERS = (
    ("test1@example.com", "Test One"),
    ("test2@example.com", "Test Two"),
    ("test3@example.com", "Test Three"),
)

# (creator, title, status, due date in days from now (negative = overdue), assignee);
# creator and assignee are indexes into DEMO_USERS.
_TASKS: tuple[tuple[int, str, TaskStatus, int | None, int | None], ...] = (
    (0, "Draft the onboarding checklist", TaskStatus.TODO, 3, 1),
    (0, "Review the pricing page copy", TaskStatus.TODO, 7, None),
    (1, "Fix the broken password reset link", TaskStatus.IN_PROGRESS, 1, 0),
    (1, "Prepare the quarterly report", TaskStatus.IN_PROGRESS, 14, 2),
    (2, "Renew the domain certificate", TaskStatus.BLOCKED, 5, 0),
    (2, "Migrate the old uploads bucket", TaskStatus.BLOCKED, -2, 1),
    (0, "Send the invoice to the design studio", TaskStatus.TODO, -3, 2),
    (1, "Update the team holiday calendar", TaskStatus.TODO, -7, 0),
    (2, "Answer the support backlog", TaskStatus.IN_PROGRESS, -1, 1),
    (0, "Publish the release notes", TaskStatus.COMPLETED, -5, 1),
    (1, "Set up the staging database", TaskStatus.COMPLETED, -14, 2),
    (2, "Book the venue for the offsite", TaskStatus.COMPLETED, None, 0),
    (0, "Replace the old logo", TaskStatus.CANCELLED, 10, None),
    (1, "Evaluate the second analytics vendor", TaskStatus.CANCELLED, -4, 0),
    (2, "Collect ideas for the next sprint", TaskStatus.TODO, None, None),
)


class SeedSettings(DatabaseSettings):
    """Only what the command needs: no JWT secret, no Redis."""

    environment: str = "local"


class SeedOutcome(StrEnum):
    SEEDED = "seeded"
    ALREADY_SEEDED = "already seeded"


class NullNotifier:
    """Seeding assigns tasks without queueing notifications, so it needs no broker."""

    async def notify(self, message: AssignmentMessage) -> None:
        return None


async def seed(database_url: str) -> SeedOutcome:
    """Create the demo users and tasks unless the demo users already exist."""
    engine = create_engine(database_url)
    try:
        factory = create_session_factory(engine)
        async with SqlUnitOfWork(factory) as uow:
            if await uow.users.get_credentials_by_email(DEMO_USERS[0][0]) is not None:
                return SeedOutcome.ALREADY_SEEDED

        clock, notifier, hasher = SystemClock(), NullNotifier(), Argon2PasswordHasher()
        users: list[User] = []
        try:
            for email, name in DEMO_USERS:
                users.append(
                    await RegisterUser(SqlUnitOfWork(factory), hasher).execute(
                        email=email, name=name, password=DEMO_PASSWORD
                    )
                )
            for creator, title, status, days, assignee in _TASKS:
                # A task cannot be created already overdue, so overdue ones start due tomorrow
                # and have their due date moved back afterwards (allowed on update).
                due = None if days is None else clock.now() + timedelta(days=max(days, 1))
                task = await CreateTask(SqlUnitOfWork(factory), clock, notifier).execute(
                    users[creator].id,
                    title=title,
                    due_date=due,
                    assignee_id=None if assignee is None else users[assignee].id,
                )
                update = UpdateTask(SqlUnitOfWork(factory), clock)
                if days is not None and days < 0:
                    await update.execute(
                        users[creator].id, task.id, due_date=clock.now() + timedelta(days=days)
                    )
                if status is not TaskStatus.TODO:
                    await update.execute(users[creator].id, task.id, status=status)
        except BaseException:
            # Do not leave half the demo data behind: a rerun would think it was complete.
            await _remove(engine, [u.id for u in users])
            raise
        return SeedOutcome.SEEDED
    finally:
        await engine.dispose()


async def _remove(engine: AsyncEngine, user_ids: list[UUID]) -> None:
    """Delete the given users and the tasks that refer to them (only what this run created)."""
    if not user_ids:
        return
    async with engine.begin() as connection:
        await connection.execute(
            delete(TaskModel).where(
                or_(TaskModel.creator_id.in_(user_ids), TaskModel.assignee_id.in_(user_ids))
            )
        )
        await connection.execute(delete(UserModel).where(UserModel.id.in_(user_ids)))


async def run(settings: SeedSettings, say: Callable[[str], None] = print) -> int:
    """Run the seed; returns the process exit code."""
    environment = settings.environment.strip().lower()
    if environment not in LOCAL_ENVIRONMENTS:
        say(
            f"Refusing to seed: TASKAPP_ENVIRONMENT is {settings.environment!r}, and demo data "
            f"is only loaded for {', '.join(sorted(LOCAL_ENVIRONMENTS))}. Nothing was changed."
        )
        return 1
    if await seed(settings.database_url) is SeedOutcome.ALREADY_SEEDED:
        say("The demo data is already there; nothing was changed.")
    else:
        say(
            f"Seeded {len(DEMO_USERS)} demo users and {len(_TASKS)} tasks. "
            f"Log in as {DEMO_USERS[0][0]} with the password {DEMO_PASSWORD}."
        )
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(SeedSettings())))


if __name__ == "__main__":
    main()
