"""Composition root: the only place that wires `api` to `infrastructure`."""

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.rate_limit import build_limiter
from taskapp.infrastructure.settings import get_settings

settings = get_settings()
app = create_app(
    title=settings.app_name,
    dependencies=build_dependencies(settings),
    limiter=build_limiter(settings.rate_limit_default, settings.redis_url),
)
