import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID, uuid4

from taskapp.domain.errors import ValidationError

EMAIL_MAX = 254
NAME_MAX = 100
PASSWORD_MIN = 8
PASSWORD_MAX = 128

# One "@", a non-empty local part and a dotted domain, no whitespace. Deliberately simple.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    name: str

    @classmethod
    def create(cls, *, email: str, name: str) -> "User":
        """Build a new user with a normalized email (trimmed, lowercase); validates the fields."""
        normalized = normalize_email(email)
        if not is_valid_email(normalized):
            raise ValidationError("email is not valid")
        clean_name = name.strip()
        if not 1 <= len(clean_name) <= NAME_MAX or _has_control_characters(clean_name):
            raise ValidationError(f"name must be 1-{NAME_MAX} printable characters")
        return cls(id=uuid4(), email=normalized, name=clean_name)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _has_control_characters(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in value)


def is_valid_email(normalized_email: str) -> bool:
    """True for an address that could be registered (and that the database can store)."""
    return (
        len(normalized_email) <= EMAIL_MAX
        and not _has_control_characters(normalized_email)
        and _EMAIL_RE.match(normalized_email) is not None
    )


def check_password(password: str) -> None:
    """Raise `ValidationError` unless the password has 8-128 characters."""
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        raise ValidationError(f"password must be {PASSWORD_MIN}-{PASSWORD_MAX} characters")
