"""Guards for the Docker setup (spec 22): profiles, services, images and the CI build."""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def services() -> dict[str, dict[str, Any]]:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    result: dict[str, dict[str, Any]] = compose["services"]
    return result


def dockerfile_stages(path: str) -> list[str]:
    text = (ROOT / path).read_text()
    return [stage for stage in re.split(r"(?m)^(?=FROM )", text) if stage.strip()]


# --- AC-01 and AC-05: the backend profile and its migration step --------------------------


def test_ac01_without_a_profile_only_postgres_and_redis_start(
    services: dict[str, dict[str, Any]],
) -> None:
    assert {name for name, service in services.items() if "profiles" not in service} == {
        "postgres",
        "redis",
    }


@pytest.mark.parametrize("name", ["migrate", "api", "worker"])
def test_ac01_the_backend_services_belong_to_the_api_and_full_profiles(
    services: dict[str, dict[str, Any]], name: str
) -> None:
    assert {"api", "full"} <= set(services[name]["profiles"])


def test_ac05_migrate_is_a_one_shot_schema_upgrade_that_waits_for_the_database(
    services: dict[str, dict[str, Any]],
) -> None:
    migrate = services["migrate"]

    assert migrate["command"] == ["alembic", "upgrade", "head"]
    assert migrate["restart"] == "no"
    assert migrate["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert "@postgres:" in migrate["environment"]["TASKAPP_DATABASE_URL"]


@pytest.mark.parametrize("name", ["api", "worker"])
def test_ac05_the_api_and_the_worker_only_start_after_a_successful_migration(
    services: dict[str, dict[str, Any]], name: str
) -> None:
    assert services[name]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"


# --- AC-02 and AC-03: the web profile ------------------------------------------------------


def test_ac02_the_web_service_is_built_from_the_frontend_and_has_its_own_profiles(
    services: dict[str, dict[str, Any]],
) -> None:
    web = services["web"]

    assert web["build"] in ("./frontend", {"context": "./frontend"})
    assert set(web["profiles"]) == {"web", "full"}
    assert web["ports"] == ["127.0.0.1:${WEB_PORT:-8080}:8080"]


def test_ac02_the_web_service_forwards_to_a_configurable_api_and_needs_nothing_else(
    services: dict[str, dict[str, Any]],
) -> None:
    web = services["web"]

    assert web["environment"]["API_UPSTREAM"] == "${API_UPSTREAM:-http://api:8000}"
    assert "host.docker.internal:host-gateway" in web["extra_hosts"]
    assert set(web["depends_on"]) == {"api"}
    assert web["healthcheck"]["test"]


def test_ac03_the_web_service_waits_for_a_healthy_api_only_when_the_api_is_part_of_the_run(
    services: dict[str, dict[str, Any]],
) -> None:
    api = services["web"]["depends_on"]["api"]

    assert api["condition"] == "service_healthy"
    assert api["required"] is False


# --- AC-04: demo data from Docker ---------------------------------------------------------


def test_ac04_seed_loads_the_demo_data_after_the_schema_exists(
    services: dict[str, dict[str, Any]],
) -> None:
    seed = services["seed"]

    assert seed["profiles"] == ["seed"]
    assert seed["command"] == ["python", "-m", "taskapp.seed"]
    assert seed["restart"] == "no"
    assert seed["environment"]["TASKAPP_ENVIRONMENT"] == "local"
    assert seed["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    assert "seed" in services["migrate"]["profiles"]


# --- AC-06: the images --------------------------------------------------------------------


def test_ac06_the_api_image_carries_the_migrations() -> None:
    dockerfile = (ROOT / "backend" / "Dockerfile").read_text()

    assert "alembic.ini" in dockerfile
    assert "migrations" in dockerfile


def test_ac06_the_web_image_is_built_in_stages_and_runs_as_a_non_root_user() -> None:
    stages = dockerfile_stages("frontend/Dockerfile")

    assert len(stages) >= 2
    final = stages[-1]
    assert re.search(r"(?m)^USER node$", final)
    assert "COPY --from=" in final
    assert "COPY . ." not in final  # no application source in the final image


def test_ac06_the_web_image_serves_through_the_small_preview_configuration() -> None:
    final = dockerfile_stages("frontend/Dockerfile")[-1]
    config = (ROOT / "frontend" / "vite.preview.config.js").read_text()

    assert "vite.preview.config.js" in final
    assert "API_UPSTREAM" in config
    assert "/api" in config
    assert "rewrite" in config


def test_ac06_the_web_container_starts_without_writing_next_to_its_own_files() -> None:
    # Vite's default config loader writes a temporary file beside the config; the non-root user
    # cannot write there, so the container must load the plain ESM config natively instead.
    final = dockerfile_stages("frontend/Dockerfile")[-1]

    assert "--configLoader" in final
    assert "native" in final


@pytest.mark.parametrize(
    ("path", "required"),
    [
        ("backend/.dockerignore", {".env", ".venv"}),
        ("frontend/.dockerignore", {"node_modules", "dist", ".env"}),
    ],
)
def test_ac06_dockerignore_files_keep_dependencies_and_secrets_out_of_the_build(
    path: str, required: set[str]
) -> None:
    entries = {line.strip().rstrip("/") for line in (ROOT / path).read_text().splitlines()}

    assert required <= entries


# --- AC-08: the CI build ------------------------------------------------------------------


def test_ac08_a_workflow_builds_the_images_when_docker_files_change() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "docker.yml").read_text())
    triggers = workflow.get("on") or workflow[True]  # YAML 1.1 reads a bare `on` as true
    paths = triggers["pull_request"]["paths"]
    commands = " ".join(
        step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
    )

    for watched in ("docker-compose.yml", "backend/Dockerfile", "frontend/Dockerfile"):
        assert watched in paths
    assert "docker compose --profile full build" in commands
