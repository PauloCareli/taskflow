"""Composition root: the only place that wires `api` to `infrastructure`."""

from taskapp.api.app import create_app
from taskapp.composition import build_dependencies
from taskapp.infrastructure.settings import get_settings

_settings = get_settings()
app = create_app(title=_settings.app_name, dependencies=build_dependencies(_settings))
