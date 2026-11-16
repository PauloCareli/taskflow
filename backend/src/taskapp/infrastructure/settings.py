from functools import lru_cache
from pathlib import Path

from limits import parse
from pydantic import Field, SecretStr, ValidationError, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    app_name: str = "Taskflow API"
    environment: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    # Required, no default: the app refuses to start without TASKAPP_JWT_SECRET (32+ characters).
    jwt_secret: SecretStr = Field(default=..., min_length=32)
    jwt_secret_file: Path = Path(".local-jwt-secret")
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "20/minute"
    celery_eager: bool = False

    def signing_secret(self) -> str:
        raise NotImplementedError

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
        problems = "; ".join(
            f"TASKAPP_{'_'.join(str(part) for part in problem['loc']).upper()}: {problem['msg']}"
            for problem in error.errors()
        )
        raise SystemExit(
            f"The settings are not valid ({problems}). Create backend/.env from "
            "backend/.env.example, and see the Configuration section of the README."
        ) from error
