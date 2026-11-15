from functools import lru_cache

from limits import parse
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TASKAPP_", env_file=".env", extra="ignore")

    app_name: str = "Taskflow API"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_default: str = "100/minute"
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
