from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+asyncpg://taskflow:taskflow@localhost:5432/taskflow"


class DatabaseSettings(BaseSettings):
    database_url: str = DEFAULT_DATABASE_URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TASKAPP_", env_file=".env", extra="ignore")

    app_name: str = "Taskflow API"
    environment: str = "local"
    database_url: str = DEFAULT_DATABASE_URL
    redis_url: str = "redis://localhost:6379/0"
    # Required, no default: the app refuses to start without TASKAPP_JWT_SECRET (32+ characters).
    jwt_secret: SecretStr = Field(default=..., min_length=32)


@lru_cache
def get_settings() -> Settings:
    return Settings()
