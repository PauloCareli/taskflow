"""Composition root: the only place that wires `api` to `infrastructure`."""

from taskapp.api.app import create_app
from taskapp.composition import build_app_limiter, build_dependencies
from taskapp.infrastructure.settings import get_settings

settings = get_settings()
app = create_app(
    title=settings.app_name,
    dependencies=build_dependencies(settings),
    limiter=build_app_limiter(settings),
    auth_limit=settings.rate_limit_auth,
)
