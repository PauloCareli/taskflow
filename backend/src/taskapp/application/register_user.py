from taskapp.application.ports import PasswordHasher, UnitOfWork
from taskapp.domain.errors import EmailTaken
from taskapp.domain.user import User, check_password


class RegisterUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher) -> None:
        self._uow = uow
        self._hasher = hasher

    async def execute(self, *, email: str, name: str, password: str) -> User:
        check_password(password)
        user = User.create(email=email, name=name)
        async with self._uow:
            if await self._uow.users.get_credentials_by_email(user.email) is not None:
                raise EmailTaken(user.email)
            # The repository also enforces uniqueness, which settles concurrent registrations.
            await self._uow.users.add(user, await self._hasher.hash(password))
            await self._uow.commit()
        return user
