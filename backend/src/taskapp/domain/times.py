from datetime import UTC, datetime

from taskapp.domain.errors import ValidationError


def check_aware(value: datetime | None, field: str) -> None:
    """Raise `ValidationError` unless `value` is timezone-aware and representable in UTC."""
    if value is None:
        return
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError(f"{field} must be timezone-aware")
    try:
        value.astimezone(UTC)
    except OverflowError as error:
        raise ValidationError(f"{field} is out of range") from error
