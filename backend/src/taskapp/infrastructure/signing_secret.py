"""A signing secret for local runs: generated once, kept in a file, reused on every start.

Only used when no `TASKAPP_JWT_SECRET` is set in a local environment (see `settings.py`).
The file is created for its owner only and is ignored by git and by Docker builds. The secret
itself is never logged.
"""

import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger("taskapp.settings")

MIN_LENGTH = 32


def load_or_create(path: Path) -> str:
    """The secret stored at `path`, creating (or replacing an invalid one) when needed.

    If the file cannot be written the secret lives in memory for this process only.
    """
    existing = _read_valid(path)
    if existing is not None:
        return existing

    secret = secrets.token_urlsafe(48)
    replacing = path.exists()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _publish(path, secret, replace=replacing)
    except FileExistsError:
        # Another process published a secret between our check and our write: use theirs.
        winner = _read_valid(path)
        if winner is not None:
            return winner
        _warn_in_memory(path)
        return secret
    except OSError:
        _warn_in_memory(path)
        return secret

    if replacing:
        logger.warning(
            "The signing secret file %s was empty or too short, so it was replaced with a new "
            "secret. Everyone who was signed in has to sign in again.",
            path,
        )
    else:
        logger.warning(
            "No TASKAPP_JWT_SECRET is set, so a signing secret was generated and saved to %s. "
            "People stay signed in across restarts while that file exists; delete it to sign "
            "everyone out, or set TASKAPP_JWT_SECRET to use your own.",
            path,
        )
    return secret


def _read_valid(path: Path) -> str | None:
    try:
        text = path.read_text().strip()
    except OSError:
        return None
    return text if len(text) >= MIN_LENGTH else None


def _publish(path: Path, secret: str, *, replace: bool) -> None:
    """Write the secret to a private temporary file, then move it into place in one step.

    A reader therefore never sees a half-written file, and when several processes start at
    once only one of them creates the file.
    """
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(secret)
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)  # fails with FileExistsError if someone else was first
    finally:
        temporary.unlink(missing_ok=True)


def _warn_in_memory(path: Path) -> None:
    logger.warning(
        "Could not save a generated signing secret to %s, so one kept in memory is used: "
        "everyone is signed out when the API restarts. Make that location writable or set "
        "TASKAPP_JWT_SECRET.",
        path,
    )
