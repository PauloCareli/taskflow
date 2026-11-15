from fastapi import FastAPI

from taskapp.api.routers import health


def create_app(title: str = "Taskflow API") -> FastAPI:
    app = FastAPI(title=title)
    app.include_router(health.router)
    return app
