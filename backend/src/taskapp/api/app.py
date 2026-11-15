from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from slowapi import Limiter

from taskapp.api.dependencies import Dependencies
from taskapp.api.errors import install_error_handlers
from taskapp.api.rate_limit import install_rate_limit
from taskapp.api.routers import auth, health, tasks, users


def _mount(app: FastAPI, router: APIRouter) -> None:
    """Register a router's routes directly on the app.

    `include_router` hides them behind a wrapper object that slowapi's middleware cannot look
    into, which would leave every routed endpoint without the default rate limit.
    """
    app.router.routes.extend(router.routes)


def create_app(
    title: str = "Taskflow API",
    dependencies: Dependencies | None = None,
    limiter: Limiter | None = None,
    auth_limit: str | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        if dependencies is not None and dependencies.shutdown is not None:
            await dependencies.shutdown()

    app = FastAPI(title=title, lifespan=lifespan)
    app.state.dependencies = dependencies
    install_error_handlers(app)
    _mount(app, health.router)
    _mount(app, auth.build_router(limiter, auth_limit))
    _mount(app, tasks.router)
    _mount(app, users.router)
    if limiter is not None:
        install_rate_limit(app, limiter)
    return app
