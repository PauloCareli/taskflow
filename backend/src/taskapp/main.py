"""Composition root: the only place that wires `api` to `infrastructure`."""

from taskapp.api.app import create_app
from taskapp.infrastructure.settings import get_settings

app = create_app(title=get_settings().app_name)
