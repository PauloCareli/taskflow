"""Guards that keep the README honest: what exists in the repository is documented in it."""

import re
from pathlib import Path

import pytest

from taskapp.infrastructure.settings import Settings
from taskapp.seed import DEMO_PASSWORD, DEMO_USERS

ROOT = Path(__file__).resolve().parents[3]
README = (ROOT / "README.md").read_text()
# Paths the README tells the reader to create themselves.
CREATED_BY_THE_READER = {"backend/.env"}
PATH_ROOTS = ("backend/", "frontend/", "spec/", "docs/", ".github/", "justfile", "docker-compose")


def just_recipes() -> list[str]:
    names = re.findall(r"^([a-z][\w-]*)(?:\s+[\w-]+)*:(?!=)", (ROOT / "justfile").read_text(), re.M)
    return [name for name in names if name != "default"]


def headings() -> list[str]:
    return [
        line.lstrip("#").strip().lower() for line in README.splitlines() if line.startswith("#")
    ]


@pytest.mark.parametrize("recipe", just_recipes())
def test_ac03_every_just_recipe_is_documented(recipe: str) -> None:
    assert f"`just {recipe}`" in README


@pytest.mark.parametrize("name", [f"TASKAPP_{field.upper()}" for field in Settings.model_fields])
def test_ac03_every_backend_setting_is_documented(name: str) -> None:
    assert f"`{name}`" in README


@pytest.mark.parametrize(
    "name",
    ["VITE_API_BASE_URL", "POSTGRES_PORT", "REDIS_PORT", "API_PORT", "WEB_PORT", "API_UPSTREAM"],
)
def test_ac03_frontend_and_compose_settings_are_documented(name: str) -> None:
    assert f"`{name}`" in README


@pytest.mark.parametrize(
    "command",
    [
        "docker compose --profile api up",
        "docker compose --profile web up",
        "docker compose --profile full up",
        "docker compose run --rm seed",
    ],
)
def test_ac07_every_docker_route_is_documented(command: str) -> None:
    assert command in README


def test_ac03_the_env_examples_cover_the_secret_and_the_frontend_setting() -> None:
    example = (ROOT / "backend" / ".env.example").read_text()

    assert "TASKAPP_JWT_SECRET" in example
    assert ".local-jwt-secret" in example
    assert "VITE_API_BASE_URL" in (ROOT / "frontend" / ".env.example").read_text()


def test_ac06_the_readme_explains_the_generated_secret_and_where_it_is_kept() -> None:
    assert ".local-jwt-secret" in README
    assert "`TASKAPP_JWT_SECRET_FILE`" in README


def test_ac03_the_demo_credentials_are_documented() -> None:
    for email, _name in DEMO_USERS:
        assert f"`{email}`" in README
    assert f"`{DEMO_PASSWORD}`" in README


def test_ac03_the_readme_has_a_troubleshooting_section() -> None:
    assert any("troubleshooting" in heading for heading in headings())


def test_ac01_the_quick_start_clones_the_real_repository_not_a_placeholder() -> None:
    assert "<repository-url>" not in README
    assert "git clone https://github.com/PauloCareli/taskflow.git" in README


def test_ac01_the_readme_is_not_marked_as_work_in_progress() -> None:
    assert "work in progress" not in README.lower()


@pytest.mark.parametrize("section", ["architecture", "key decisions", "ai tooling"])
def test_ac04_the_readme_has_the_required_sections(section: str) -> None:
    assert any(section in heading for heading in headings())


def test_ac05_the_readme_links_the_ai_logs() -> None:
    for log in ("docs/ai/prompts.md", "docs/ai/corrections.md", "docs/ai/usage.md"):
        assert log in README


def test_ac05_the_usage_page_says_the_figures_were_not_recorded() -> None:
    usage = (ROOT / "docs" / "ai" / "usage.md").read_text().lower()

    assert "not recorded" in usage
    assert "estimate" in usage


def test_ac06_no_stale_spec_placeholder_remains() -> None:
    assert not (ROOT / "docs" / "spec.md").exists()


def test_ac06_every_relative_link_and_file_path_in_the_readme_exists() -> None:
    links = [
        target.split("#")[0]
        for target in re.findall(r"\]\(([^)\s]+)\)", README)
        if not target.startswith(("http://", "https://", "#", "mailto:"))
    ]
    quoted = [
        token
        for token in re.findall(r"`([^`\s]+)`", README)
        if token.startswith(PATH_ROOTS) and not re.search(r"[<>{}*$|]", token)
    ]

    missing = [
        path
        for path in {*links, *quoted}
        if path and path not in CREATED_BY_THE_READER and not (ROOT / path.rstrip("/")).exists()
    ]

    assert missing == []
