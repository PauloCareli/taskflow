from celery import Celery
from celery.app.utils import find_app

from taskapp.infrastructure.celery_app import create_celery_app
from taskapp.infrastructure.settings import Settings


def test_ac06_the_broker_is_the_configured_redis_url() -> None:
    app = create_celery_app(Settings(redis_url="redis://cache.example:6380/3"))

    assert app.conf.broker_url == "redis://cache.example:6380/3"


def test_ac06_only_json_is_accepted_and_returned() -> None:
    app = create_celery_app(Settings())

    assert app.conf.task_serializer == "json"
    assert app.conf.result_serializer == "json"
    assert list(app.conf.accept_content) == ["json"]


def test_ac06_creating_the_app_does_not_connect_to_the_broker() -> None:
    # Port 1 refuses connections; any connection attempt at import time would raise.
    app = create_celery_app(Settings(redis_url="redis://127.0.0.1:1/0"))

    assert isinstance(app, Celery)


def test_ac06_eager_mode_runs_tasks_in_process_without_a_broker() -> None:
    app = create_celery_app(Settings(celery_eager=True, redis_url="redis://127.0.0.1:1/0"))

    @app.task
    def add(a: int, b: int) -> int:
        return a + b

    assert add.delay(2, 3).get() == 5


def test_ac06_without_eager_mode_tasks_are_sent_to_the_broker() -> None:
    app = create_celery_app(Settings(celery_eager=False))

    assert app.conf.task_always_eager is False


def test_ac07_the_worker_entrypoint_module_exposes_the_app() -> None:
    app = find_app("taskapp.infrastructure.celery_app")

    assert isinstance(app, Celery)
    assert app.main == "taskapp"
