class DomainError(Exception):
    """Base class for business-rule violations."""


class ValidationError(DomainError):
    """Input breaks a field rule (length, range, timezone)."""


class InvalidTransition(DomainError):
    """The requested status change is not allowed."""


class PermissionDenied(DomainError):
    """The caller can see the task but may not perform this action."""


class TaskNotFound(DomainError):
    """The task does not exist or is not visible to the caller."""


class UserNotFound(DomainError):
    """The referenced user does not exist."""


class EmailTaken(DomainError):
    """A user with this email is already registered."""


class InvalidCredentials(DomainError):
    """Email or password is wrong; deliberately does not say which."""


class InvalidToken(DomainError):
    """The access token is missing, malformed, expired or not trusted."""
