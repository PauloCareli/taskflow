from celery import Celery

from taskapp.infrastructure.settings import Settings, get_settings


def create_celery_app(settings: Settings) -> Celery:
    return Celery("unconfigured")


celery_app = create_celery_app(get_settings())
