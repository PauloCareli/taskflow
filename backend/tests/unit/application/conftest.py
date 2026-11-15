from datetime import UTC, datetime
from uuid import uuid4

import pytest

from taskapp.domain.user import User
from tests.fakes import (
    FixedClock,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
    RecordingNotifier,
)

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


@pytest.fixture
def alice() -> User:
    return User(id=uuid4(), email="alice@example.com", name="alice")


@pytest.fixture
def bob() -> User:
    return User(id=uuid4(), email="bob@example.com", name="bob")


@pytest.fixture
def carol() -> User:
    return User(id=uuid4(), email="carol@example.com", name="carol")


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def tasks() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def uow(tasks: InMemoryTaskRepository, alice: User, bob: User, carol: User) -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(tasks, InMemoryUserRepository([alice, bob, carol]))


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()
