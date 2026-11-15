from pathlib import Path

import pytest
from pydantic import ValidationError

from taskapp.infrastructure.settings import Settings


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No TASKAPP_* variables and no .env file in the working directory."""
    for name in (
        "APP_NAME",
        "ENVIRONMENT",
        "DATABASE_URL",
        "REDIS_URL",
        "RATE_LIMIT_DEFAULT",
        "CELERY_EAGER",
    ):
        monkeypatch.delenv(f"TASKAPP_{name}", raising=False)
    monkeypatch.chdir(tmp_path)


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.environment == "local"
    assert settings.redis_url.startswith("redis://")


def test_settings_read_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_ENVIRONMENT", "test")

    assert Settings().environment == "test"


def test_ac04_default_rate_limit_is_100_per_minute() -> None:
    assert Settings().rate_limit_default == "100/minute"


def test_ac04_rate_limit_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_RATE_LIMIT_DEFAULT", "5/second")

    assert Settings().rate_limit_default == "5/second"


@pytest.mark.parametrize("value", ["", "lots", "100", "100/fortnight"])
def test_ac04_an_invalid_rate_limit_fails_and_names_the_setting(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("TASKAPP_RATE_LIMIT_DEFAULT", value)

    with pytest.raises(ValidationError, match="TASKAPP_RATE_LIMIT_DEFAULT"):
        Settings()


def test_ac06_celery_runs_tasks_through_the_broker_by_default() -> None:
    assert Settings().celery_eager is False


def test_ac06_celery_eager_can_be_switched_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_CELERY_EAGER", "true")

    assert Settings().celery_eager is True
