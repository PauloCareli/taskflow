from fastapi import FastAPI
from slowapi import Limiter

from taskapp.api.rate_limit import install_rate_limit
from taskapp.api.routers import health


def create_app(title: str = "Taskflow API", limiter: Limiter | None = None) -> FastAPI:
    app = FastAPI(title=title)
    app.include_router(health.router)
    if limiter is not None:
        install_rate_limit(app, limiter)
    return app
