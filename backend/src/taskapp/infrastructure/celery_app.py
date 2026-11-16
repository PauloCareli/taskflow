from celery import Celery

from taskapp.infrastructure.settings import Settings, get_settings
from taskapp.infrastructure.tasks import register_tasks

# For the side that publishes (the API): fail fast when the broker is down. The notifier does
# its own bounded retries, and a request must not wait on Celery's default patience. The worker
# must not use these: its blocking poll for new tasks takes about a second and would time out.
_PUBLISHER_OPTIONS = {
    "task_publish_retry": False,
    "broker_connection_timeout": 0.3,
    "broker_transport_options": {
        "socket_connect_timeout": 0.3,
        "socket_timeout": 0.3,
        # kombu's own connect retries when a connection is first used.
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0.1,
        "interval_max": 0.2,
    },
}


def create_celery_app(settings: Settings, *, publisher: bool = False) -> Celery:
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
    if publisher:
        app.conf.update(_PUBLISHER_OPTIONS)
    return app


celery_app = create_celery_app(get_settings())
register_tasks(
    celery_app
)  # so a worker started with `-A taskapp.infrastructure.celery_app` has them
