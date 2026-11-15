import pytest

from taskapp.infrastructure.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.environment == "local"
    assert settings.redis_url.startswith("redis://")


def test_settings_read_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_ENVIRONMENT", "test")

    assert Settings().environment == "test"
