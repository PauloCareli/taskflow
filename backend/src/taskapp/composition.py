"""Composition root: builds the `api` dependencies from `infrastructure` adapters."""

from slowapi import Limiter

from taskapp.api.dependencies import Dependencies
from taskapp.infrastructure.celery_app import create_celery_app
from taskapp.infrastructure.celery_notifier import CeleryNotifier
from taskapp.infrastructure.db.session import create_engine, create_session_factory
from taskapp.infrastructure.db.unit_of_work import SqlUnitOfWork
from taskapp.infrastructure.rate_limit import build_limiter, user_or_address_key
from taskapp.infrastructure.security import Argon2PasswordHasher, JwtTokenService, SystemClock
from taskapp.infrastructure.settings import Settings
from taskapp.infrastructure.tasks import register_tasks


def build_app_limiter(settings: Settings) -> Limiter:
    """The default limit, counted per signed-in user and per address for anonymous requests."""
    tokens = JwtTokenService(settings.jwt_secret.get_secret_value(), SystemClock())
    return build_limiter(
        settings.rate_limit_default,
        settings.redis_url,
        key_func=user_or_address_key(tokens),
    )


def build_dependencies(settings: Settings) -> Dependencies:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    clock = SystemClock()
    return Dependencies(
        uow_factory=lambda: SqlUnitOfWork(session_factory),
        hasher=Argon2PasswordHasher(),
        tokens=JwtTokenService(settings.jwt_secret.get_secret_value(), clock),
        clock=clock,
        notifier=CeleryNotifier(register_tasks(create_celery_app(settings))),
        shutdown=engine.dispose,
    )
