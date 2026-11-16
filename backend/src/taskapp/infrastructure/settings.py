from functools import lru_cache
from pathlib import Path
from typing import Self

from limits import parse
from pydantic import (
    PrivateAttr,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import ErrorDetails
from pydantic_settings import BaseSettings, SettingsConfigDict

from taskapp.infrastructure import signing_secret

DEFAULT_DATABASE_URL = "postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow"
# Environments where demo data may be seeded and a signing secret may be generated.
LOCAL_ENVIRONMENTS = frozenset({"local", "dev", "development", "test"})


class DatabaseSettings(BaseSettings):
    """Just the database URL, so tools such as migrations need no other setting.

    Read from `TASKAPP_DATABASE_URL`, then `.env`, exactly as the app does.
    """

    model_config = SettingsConfigDict(env_prefix="TASKAPP_", env_file=".env", extra="ignore")

    database_url: str = DEFAULT_DATABASE_URL


class Settings(DatabaseSettings):
    # A mistyped secret must not be echoed back in an error message.
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    app_name: str = "Taskflow API"
    environment: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    # Optional in local environments, where a secret is generated and kept in `jwt_secret_file`
    # (see `signing_secret()`); required (32+ characters) everywhere else.
    jwt_secret: SecretStr | None = None
    jwt_secret_file: Path = Path(".local-jwt-secret")
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "20/minute"
    celery_eager: bool = False

    _signing_secret: str | None = PrivateAttr(default=None)

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _an_empty_secret_is_no_secret(cls, value: object) -> object:
        # `docker compose` passes an empty value through when the host has none.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _a_secret_must_be_long_enough(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and len(value.get_secret_value()) < signing_secret.MIN_LENGTH:
            msg = f"TASKAPP_JWT_SECRET must be at least {signing_secret.MIN_LENGTH} characters"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _a_secret_is_required_outside_local_environments(self) -> Self:
        if self.jwt_secret is None and self.environment.strip().lower() not in LOCAL_ENVIRONMENTS:
            msg = (
                f"TASKAPP_JWT_SECRET is required when TASKAPP_ENVIRONMENT is "
                f"{self.environment!r}; only {', '.join(sorted(LOCAL_ENVIRONMENTS))} may "
                "generate one"
            )
            raise ValueError(msg)
        return self

    def signing_secret(self) -> str:
        """The secret that signs access tokens; the same value for the life of this object.

        An explicit `TASKAPP_JWT_SECRET` wins. Otherwise (local environments only, see the
        validator above) one is generated and kept in `jwt_secret_file`.
        """
        if self.jwt_secret is not None:
            return self.jwt_secret.get_secret_value()
        if self._signing_secret is None:
            self._signing_secret = signing_secret.load_or_create(self.jwt_secret_file)
        return self._signing_secret

    @field_validator("rate_limit_default", "rate_limit_auth")
    @classmethod
    def _valid_rate_limit(cls, value: str, info: ValidationInfo) -> str:
        try:
            parse(value)
        except ValueError as error:
            name = f"TASKAPP_{(info.field_name or '').upper()}"
            msg = f"{name} must look like '100/minute', got {value!r}"
            raise ValueError(msg) from error
        return value


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        problems = "; ".join(_describe(problem) for problem in error.errors())
        raise SystemExit(
            f"The settings are not valid ({problems}). See the Configuration section of the "
            "README (backend/.env.example lists the settings)."
        ) from error


def _describe(problem: ErrorDetails) -> str:
    where = "_".join(str(part) for part in problem["loc"])
    message = problem["msg"].removeprefix("Value error, ")
    return f"TASKAPP_{where.upper()}: {message}" if where else message
