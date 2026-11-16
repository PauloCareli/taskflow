"""The signing secret (spec 26): generated and kept in a file locally, required elsewhere."""

import logging
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from taskapp.infrastructure.celery_app import create_celery_app
from taskapp.infrastructure.security import JwtTokenService
from taskapp.infrastructure.settings import LOCAL_ENVIRONMENTS, Settings, get_settings
from tests.fakes import FixedClock

STRONG = "an-explicit-secret-with-more-than-32-characters"
LOGGER = "taskapp.settings"


@pytest.fixture(autouse=True)
def isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No TASKAPP_* variables and a working directory of its own."""
    for name in ("JWT_SECRET", "JWT_SECRET_FILE", "ENVIRONMENT"):
        monkeypatch.delenv(f"TASKAPP_{name}", raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def secret_file(tmp_path: Path) -> Path:
    return tmp_path / "state" / "jwt-secret"


def modified_at(path: Path) -> int:
    return path.stat().st_mtime_ns


def warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == LOGGER and r.levelno == logging.WARNING]


# --- AC-01: a local start without a secret generates and keeps one ------------------------


def test_ac01_the_secret_is_generated_into_a_file_only_its_owner_can_use(
    secret_file: Path,
) -> None:
    secret = Settings(jwt_secret_file=secret_file).signing_secret()

    assert len(secret) >= 32
    assert secret_file.read_text() == secret
    assert stat.S_IMODE(secret_file.stat().st_mode) == 0o600


def test_ac01_one_warning_names_the_file_and_says_how_to_sign_everyone_out(
    secret_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    settings = Settings(jwt_secret_file=secret_file)

    with caplog.at_level(logging.INFO, logger=LOGGER):
        secret = settings.signing_secret()
        settings.signing_secret()

    [warning] = warnings(caplog)
    assert str(secret_file) in warning.getMessage()
    assert "delet" in warning.getMessage().lower()
    assert secret not in warning.getMessage()


@pytest.mark.parametrize("environment", [*sorted(LOCAL_ENVIRONMENTS), " Local ", "LOCAL"])
def test_ac01_every_local_environment_may_generate_a_secret(
    secret_file: Path, environment: str
) -> None:
    settings = Settings(environment=environment, jwt_secret_file=secret_file)

    assert len(settings.signing_secret()) >= 32


def test_ac01_an_empty_secret_counts_as_unset(secret_file: Path) -> None:
    settings = Settings(jwt_secret="", jwt_secret_file=secret_file)  # type: ignore[arg-type]

    assert settings.signing_secret() == secret_file.read_text()


# --- AC-02: a restart reuses the secret ---------------------------------------------------


async def test_ac02_a_restart_reuses_the_file_so_earlier_tokens_stay_valid(
    secret_file: Path,
) -> None:
    clock = FixedClock(datetime.now(UTC))
    first = Settings(jwt_secret_file=secret_file).signing_secret()
    before = modified_at(secret_file)
    token = (await JwtTokenService(first, clock).issue(uuid4())).token

    second = Settings(jwt_secret_file=secret_file).signing_secret()

    assert second == first
    assert modified_at(secret_file) == before
    assert await JwtTokenService(second, clock).verify(token)


def test_ac02_starting_twice_logs_no_warning_the_second_time(
    secret_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    Settings(jwt_secret_file=secret_file).signing_secret()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        Settings(jwt_secret_file=secret_file).signing_secret()

    assert warnings(caplog) == []


# --- AC-03: a bad or unwritable file ------------------------------------------------------


@pytest.mark.parametrize("content", ["", "too-short", "   \n"])
def test_ac03_an_invalid_file_is_replaced_with_a_new_secret_and_a_warning(
    secret_file: Path, caplog: pytest.LogCaptureFixture, content: str
) -> None:
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text(content)

    with caplog.at_level(logging.INFO, logger=LOGGER):
        secret = Settings(jwt_secret_file=secret_file).signing_secret()

    assert len(secret) >= 32
    assert secret_file.read_text() == secret
    assert stat.S_IMODE(secret_file.stat().st_mode) == 0o600
    assert len(warnings(caplog)) == 1


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write anywhere")
def test_ac03_an_unwritable_location_falls_back_to_a_secret_kept_in_memory(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    target = locked / "jwt-secret"
    settings = Settings(jwt_secret_file=target)

    try:
        with caplog.at_level(logging.INFO, logger=LOGGER):
            secret = settings.signing_secret()
            again = settings.signing_secret()
    finally:
        locked.chmod(0o700)

    assert len(secret) >= 32
    assert again == secret
    assert not target.exists()
    [warning] = warnings(caplog)
    assert "memory" in warning.getMessage().lower()
    assert secret not in warning.getMessage()


# --- AC-04: elsewhere a secret is required ------------------------------------------------


@pytest.mark.parametrize("environment", ["production", " Production ", "staging", "prod", "x", ""])
def test_ac04_other_environments_refuse_to_start_without_a_secret(
    secret_file: Path, environment: str
) -> None:
    with pytest.raises(ValidationError, match="TASKAPP_JWT_SECRET"):
        Settings(environment=environment, jwt_secret_file=secret_file)

    assert not secret_file.exists()


def test_ac04_a_secret_file_is_not_read_outside_local_environments(secret_file: Path) -> None:
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text(STRONG)

    with pytest.raises(ValidationError, match="TASKAPP_JWT_SECRET"):
        Settings(environment="production", jwt_secret_file=secret_file)

    assert secret_file.read_text() == STRONG


@pytest.mark.parametrize("environment", ["local", "production"])
def test_ac04_a_short_secret_is_an_error_everywhere_and_is_not_echoed(
    secret_file: Path, environment: str
) -> None:
    mistyped = "too-short-secret"

    with pytest.raises(ValidationError, match="TASKAPP_JWT_SECRET") as error:
        Settings(
            environment=environment,
            jwt_secret=mistyped,  # type: ignore[arg-type]
            jwt_secret_file=secret_file,
        )

    assert mistyped not in str(error.value)
    assert not secret_file.exists()


def test_ac04_the_start_up_message_names_the_setting_and_points_to_the_readme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TASKAPP_ENVIRONMENT", "production")
    get_settings.cache_clear()

    try:
        with pytest.raises(SystemExit) as stopped:
            get_settings()
    finally:
        get_settings.cache_clear()

    assert "TASKAPP_JWT_SECRET" in str(stopped.value)
    assert "README" in str(stopped.value)


# --- AC-05: an explicit secret is used as it is -------------------------------------------


@pytest.mark.parametrize("environment", ["local", "production"])
def test_ac05_an_explicit_secret_is_used_and_the_file_is_never_touched(
    secret_file: Path, environment: str
) -> None:
    settings = Settings(
        environment=environment,
        jwt_secret=STRONG,  # type: ignore[arg-type]
        jwt_secret_file=secret_file,
    )

    assert settings.signing_secret() == STRONG
    assert not secret_file.exists()


# --- AC-06: random, shared within a process, never logged ---------------------------------


def test_ac06_each_generated_secret_is_random_with_enough_entropy(tmp_path: Path) -> None:
    secrets_seen = {
        Settings(jwt_secret_file=tmp_path / f"secret-{n}").signing_secret() for n in range(5)
    }

    assert len(secrets_seen) == 5
    assert all(len(s.encode()) >= 32 for s in secrets_seen)


def test_ac06_two_processes_starting_together_end_up_with_the_same_secret(
    secret_file: Path,
) -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(lambda _: Settings(jwt_secret_file=secret_file).signing_secret(), range(8))
        )

    assert len(set(results)) == 1
    assert secret_file.read_text() == results[0]


def test_ac06_the_secret_never_appears_in_logs_or_in_the_settings_text(
    secret_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    settings = Settings(jwt_secret_file=secret_file)

    with caplog.at_level(logging.DEBUG):
        secret = settings.signing_secret()

    assert secret not in caplog.text
    assert secret not in repr(settings)
    assert secret not in str(settings)


# --- AC-07: nothing that does not issue or verify tokens creates the file ----------------


def test_ac07_building_the_settings_and_the_celery_app_creates_no_file(
    secret_file: Path, tmp_path: Path
) -> None:
    settings = Settings(jwt_secret_file=secret_file)

    create_celery_app(settings)

    assert not secret_file.exists()
    assert list(tmp_path.iterdir()) == []
