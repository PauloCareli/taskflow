from dataclasses import dataclass
from uuid import UUID

EMAIL_MAX = 254
NAME_MAX = 100
PASSWORD_MIN = 8
PASSWORD_MAX = 128


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    name: str

    @classmethod
    def create(cls, *, email: str, name: str) -> "User":
        """Build a new user with a normalized email (trimmed, lowercase); validates the fields."""
        raise NotImplementedError


def normalize_email(email: str) -> str:
    raise NotImplementedError


def check_password(password: str) -> None:
    """Raise `ValidationError` unless the password has 8-128 characters."""
    raise NotImplementedError
