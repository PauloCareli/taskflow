from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from taskapp.infrastructure.db.repositories import SqlTaskRepository, SqlUserRepository


class SqlUnitOfWork:
    """One database session and transaction. Nothing is stored unless `commit` is called."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._tasks: SqlTaskRepository | None = None
        self._users: SqlUserRepository | None = None

    @property
    def tasks(self) -> SqlTaskRepository:
        if self._tasks is None:
            raise RuntimeError("the unit of work is not active")
        return self._tasks

    @property
    def users(self) -> SqlUserRepository:
        if self._users is None:
            raise RuntimeError("the unit of work is not active")
        return self._users

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self._tasks = SqlTaskRepository(self._session)
        self._users = SqlUserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self._session
        self._session = self._tasks = self._users = None
        if session is not None:
            try:
                await session.rollback()  # discards anything that was not committed
            finally:
                await session.close()

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("the unit of work is not active")
        await self._session.commit()
