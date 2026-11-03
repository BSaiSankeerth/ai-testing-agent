from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env."""

    app_name: str = "AI Testing Agent API"
    environment: str = "development"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5174"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create Settings once and reuse it everywhere."""
    return Settings()