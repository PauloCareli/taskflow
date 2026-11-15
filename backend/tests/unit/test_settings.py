from pathlib import Path

import pytest

from taskapp.infrastructure.settings import Settings


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No TASKAPP_* variables and no .env file in the working directory."""
    for name in ("APP_NAME", "ENVIRONMENT", "DATABASE_URL", "REDIS_URL"):
        monkeypatch.delenv(f"TASKAPP_{name}", raising=False)
    monkeypatch.chdir(tmp_path)


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.environment == "local"
    assert settings.redis_url.startswith("redis://")


def test_settings_read_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_ENVIRONMENT", "test")

    assert Settings().environment == "test"
