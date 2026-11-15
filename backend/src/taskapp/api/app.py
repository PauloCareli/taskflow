from fastapi import FastAPI

from taskapp.api.dependencies import Dependencies
from taskapp.api.routers import auth, health


def create_app(title: str = "Taskflow API", dependencies: Dependencies | None = None) -> FastAPI:
    app = FastAPI(title=title)
    app.state.dependencies = dependencies
    app.include_router(health.router)
    app.include_router(auth.router)
    return app
