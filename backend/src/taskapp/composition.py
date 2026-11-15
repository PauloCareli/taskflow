"""Composition root: builds the `api` dependencies from `infrastructure` adapters."""

from taskapp.api.dependencies import Dependencies
from taskapp.infrastructure.settings import Settings


def build_dependencies(settings: Settings) -> Dependencies:
    raise NotImplementedError
