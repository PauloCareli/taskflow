from slowapi import Limiter
from slowapi.util import get_remote_address


def build_limiter(default_limit: str, storage_uri: str) -> Limiter:
    """Limiter keyed by client IP; a failing storage never blocks requests."""
    return Limiter(
        key_func=get_remote_address,
        default_limits=[default_limit],
        storage_uri=storage_uri,
        swallow_errors=True,
    )
