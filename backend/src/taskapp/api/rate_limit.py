import math
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from taskapp.api.routers import health


def _retry_after_seconds(request: Request, limiter: Limiter) -> int:
    item, args = request.state.view_rate_limit
    try:
        reset_at, _remaining = limiter.limiter.get_window_stats(item, *args)
    except Exception:  # the storage may fail between the check and here
        return max(1, int(item.get_expiry()))
    return max(1, math.ceil(reset_at - time.time()))


def _rate_limited(request: Request, exc: Exception) -> Response:
    limiter: Limiter = request.app.state.limiter
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Too many requests. Try again later.",
                "details": [],
            }
        },
        headers={"Retry-After": str(_retry_after_seconds(request, limiter))},
    )


class _FailOpenSlowAPIMiddleware(SlowAPIMiddleware):
    """SlowAPI skips the check when the storage fails but then reads a state it never set."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.view_rate_limit = None
        return await super().dispatch(request, call_next)


def install_rate_limit(app: FastAPI, limiter: Limiter) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limited)
    app.add_middleware(_FailOpenSlowAPIMiddleware)
    limiter.exempt(health.health)  # type: ignore[no-untyped-call]  # slowapi is untyped
