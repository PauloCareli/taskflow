from pathlib import Path

import pytest
from pydantic import ValidationError

from taskapp.infrastructure.settings import DatabaseSettings, Settings

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No TASKAPP_* variables and no .env file in the working directory."""
    for name in ("APP_NAME", "ENVIRONMENT", "DATABASE_URL", "REDIS_URL", "JWT_SECRET"):
        monkeypatch.delenv(f"TASKAPP_{name}", raising=False)
    monkeypatch.setenv("TASKAPP_JWT_SECRET", SECRET)
    monkeypatch.chdir(tmp_path)


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.environment == "local"
    assert settings.redis_url.startswith("redis://")


def test_settings_read_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKAPP_ENVIRONMENT", "test")

    assert Settings().environment == "test"


def test_ac08_database_settings_read_the_dotenv_file_without_needing_the_jwt_secret(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("TASKAPP_JWT_SECRET")
    (tmp_path / ".env").write_text("TASKAPP_DATABASE_URL=postgresql+asyncpg://u:p@db:5432/other\n")

    assert DatabaseSettings().database_url == "postgresql+asyncpg://u:p@db:5432/other"


def test_ac08_the_environment_wins_over_the_dotenv_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text("TASKAPP_DATABASE_URL=postgresql+asyncpg://u:p@db:5432/other\n")
    monkeypatch.setenv("TASKAPP_DATABASE_URL", "postgresql+asyncpg://u:p@db:5432/from_env")

    assert DatabaseSettings().database_url.endswith("/from_env")


def test_ac05_the_jwt_secret_is_read_from_the_environment_and_not_printed() -> None:
    settings = Settings()

    assert settings.jwt_secret.get_secret_value() == SECRET
    assert SECRET not in repr(settings)


def test_ac05_a_missing_jwt_secret_stops_startup_naming_the_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TASKAPP_JWT_SECRET")

    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings()


@pytest.mark.parametrize("secret", ["", "too-short"])
def test_ac05_an_empty_or_short_jwt_secret_stops_startup(
    monkeypatch: pytest.MonkeyPatch, secret: str
) -> None:
    monkeypatch.setenv("TASKAPP_JWT_SECRET", secret)

    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings()
