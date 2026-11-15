import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
CELERY_APP = "taskapp.infrastructure.celery_app"


@pytest.fixture(scope="module")
def services() -> dict[str, dict[str, Any]]:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    result: dict[str, dict[str, Any]] = compose["services"]
    return result


def test_ac08_postgres_and_redis_start_without_a_profile(
    services: dict[str, dict[str, Any]],
) -> None:
    assert "profiles" not in services["postgres"]
    assert "profiles" not in services["redis"]


@pytest.mark.parametrize("name", ["api", "worker"])
def test_ac08_api_and_worker_only_start_with_the_full_profile(
    services: dict[str, dict[str, Any]], name: str
) -> None:
    assert services[name]["profiles"] == ["full"]
    assert services[name]["build"] in ("./backend", {"context": "./backend"})


@pytest.mark.parametrize("name", ["api", "worker"])
def test_ac08_api_and_worker_wait_for_healthy_dependencies(
    services: dict[str, dict[str, Any]], name: str
) -> None:
    depends = services[name]["depends_on"]

    for dependency in ("postgres", "redis"):
        assert depends[dependency]["condition"] == "service_healthy"


@pytest.mark.parametrize("name", ["api", "worker"])
def test_ac08_api_and_worker_report_health_and_use_service_hostnames(
    services: dict[str, dict[str, Any]], name: str
) -> None:
    service = services[name]

    assert service["healthcheck"]["test"]
    assert service["environment"]["TASKAPP_REDIS_URL"].startswith("redis://redis:")
    assert "@postgres:" in service["environment"]["TASKAPP_DATABASE_URL"]


def test_ac08_the_api_is_checked_through_health_and_the_worker_through_a_celery_ping(
    services: dict[str, dict[str, Any]],
) -> None:
    assert "/health" in " ".join(services["api"]["healthcheck"]["test"])
    worker_check = " ".join(services["worker"]["healthcheck"]["test"])
    assert CELERY_APP in worker_check
    assert "ping" in worker_check


def test_ac08_the_worker_runs_the_celery_app_and_nothing_runs_migrations(
    services: dict[str, dict[str, Any]],
) -> None:
    command = " ".join(services["worker"]["command"])

    assert f"-A {CELERY_APP}" in command
    assert "worker" in command
    for name in ("api", "worker"):
        assert "alembic" not in str(services[name].get("command", ""))


def test_ac07_just_worker_starts_a_celery_worker_for_the_project_app() -> None:
    justfile = (ROOT / "justfile").read_text()
    recipe = re.search(r"^worker:\n((?:[ \t]+.*\n?)+)", justfile, re.MULTILINE)

    assert recipe is not None
    assert f"celery -A {CELERY_APP} worker" in recipe.group(1)
