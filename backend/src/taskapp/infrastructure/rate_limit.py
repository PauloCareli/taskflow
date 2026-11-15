from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address

# slowapi talks to Redis synchronously; never let an unresponsive Redis stall the event loop.
# (slowapi types these as str, but they are passed straight to redis-py.)
_STORAGE_OPTIONS: dict[str, Any] = {"socket_connect_timeout": 0.2, "socket_timeout": 0.2}


def build_limiter(default_limit: str, storage_uri: str) -> Limiter:
    """Limiter keyed by client IP; a failing storage never blocks requests."""
    return Limiter(
        key_func=get_remote_address,
        default_limits=[default_limit],
        storage_uri=storage_uri,
        swallow_errors=True,
        storage_options=_STORAGE_OPTIONS,
    )
