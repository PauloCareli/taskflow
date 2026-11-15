from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from taskapp.infrastructure.db.repositories import SqlTaskRepository, SqlUserRepository


class SqlUnitOfWork:
    """One database session and transaction. Nothing is stored unless `commit` is called."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @property
    def tasks(self) -> SqlTaskRepository:
        raise NotImplementedError

    @property
    def users(self) -> SqlUserRepository:
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError
