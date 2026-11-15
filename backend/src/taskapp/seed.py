"""Seed command: `python -m taskapp.seed` (see `just seed`).

Loads three demo users and a set of tasks through the same use cases the API uses. Part of the
composition root, so it may use `infrastructure` directly.
"""

import asyncio
import sys
from collections.abc import Callable
from enum import StrEnum

from taskapp.application.ports import AssignmentMessage
from taskapp.infrastructure.settings import DatabaseSettings

DEMO_PASSWORD = "password123"  # noqa: S105 (documented demo credential, not a secret)
DEMO_USERS = (
    ("test1@example.com", "Test One"),
    ("test2@example.com", "Test Two"),
    ("test3@example.com", "Test Three"),
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
    raise NotImplementedError


async def run(settings: SeedSettings, say: Callable[[str], None] = print) -> int:
    """Run the seed; returns the process exit code."""
    raise NotImplementedError


def main() -> None:
    sys.exit(asyncio.run(run(SeedSettings())))


if __name__ == "__main__":
    main()
