from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env."""

    app_name: str = "AI Testing Agent API"
    environment: str = "development"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5174"]
    database_url: str

    llm_provider: str = "groq"
    groq_api_key: SecretStr | None = None
    llm_model: str = "openai/gpt-oss-120b"

    approved_targets: list[str] = ["http://localhost:3000"]
    approved_api_origins: list[str] = ["http://localhost:8000"]

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    browser_headless: bool = True
    browser_slow_mo_ms: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create Settings once and reuse it everywhere."""
    return Settings()