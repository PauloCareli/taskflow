from collections.abc import Callable
from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from taskapp.domain.errors import InvalidToken
from taskapp.infrastructure.security import JwtTokenService

# slowapi talks to Redis synchronously; never let an unresponsive Redis stall the event loop.
# (slowapi types these as str, but they are passed straight to redis-py.)
_STORAGE_OPTIONS: dict[str, Any] = {"socket_connect_timeout": 0.2, "socket_timeout": 0.2}


def user_or_address_key(tokens: JwtTokenService) -> Callable[[Request], str]:
    """Count a request against the signed-in user, or else against the client address.

    The token's signature and expiry are checked (no database lookup), so a forged or stale
    token falls back to the address and can never spend another user's budget.
    """

    def key(request: Request) -> str:
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme.lower() == "bearer" and token.strip():
            try:
                return f"user:{tokens.user_id_from(token.strip())}"
            except InvalidToken:
                pass  # not a token we issued (or expired): treat the request as anonymous
        return f"ip:{get_remote_address(request)}"

    return key


def build_limiter(
    default_limit: str,
    storage_uri: str,
    key_func: Callable[[Request], str] = get_remote_address,
) -> Limiter:
    """Limiter with the given key (client IP by default); a failing storage never blocks."""
    return Limiter(
        key_func=key_func,
        default_limits=[default_limit],
        storage_uri=storage_uri,
        swallow_errors=True,
        storage_options=_STORAGE_OPTIONS,
    )
