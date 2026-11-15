from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from taskapp.api.dependencies import Dependencies
from taskapp.api.errors import install_error_handlers
from taskapp.api.routers import auth, health


def create_app(title: str = "Taskflow API", dependencies: Dependencies | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        if dependencies is not None and dependencies.shutdown is not None:
            await dependencies.shutdown()

    app = FastAPI(title=title, lifespan=lifespan)
    app.state.dependencies = dependencies
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    return app
