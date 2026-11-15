from celery import Celery

from taskapp.infrastructure.settings import Settings, get_settings


def create_celery_app(settings: Settings) -> Celery:
    """Celery on the Redis broker. Nothing connects until a task is sent or a worker starts."""
    app = Celery("taskapp", broker=settings.redis_url)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_always_eager=settings.celery_eager,
        task_eager_propagates=True,
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = create_celery_app(get_settings())
