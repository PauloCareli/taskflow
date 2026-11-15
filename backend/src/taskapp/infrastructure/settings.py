from functools import lru_cache

from limits import parse
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow"


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
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "20/minute"
    celery_eager: bool = False

    @field_validator("rate_limit_default")
    @classmethod
    def _valid_rate_limit(cls, value: str) -> str:
        try:
            parse(value)
        except ValueError as error:
            msg = f"TASKAPP_RATE_LIMIT_DEFAULT must look like '100/minute', got {value!r}"
            raise ValueError(msg) from error
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
