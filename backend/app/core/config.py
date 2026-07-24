"""Environment-backed application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings with safe development defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AVENWARD_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://avenward:change-me@localhost:5432/avenward"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    readiness_timeout_seconds: float = Field(default=2.0, gt=0, le=10)
    session_hours: int = Field(default=12, ge=1, le=168)
    upload_max_bytes: int = Field(default=2_000_000, ge=1024, le=10_000_000)
    webhook_max_events: int = Field(default=500, ge=1, le=5000)
    demo_ingest_key: str = Field(default="avenward-demo-ingest-key", min_length=16, max_length=128)
    worker_poll_seconds: float = Field(default=1.0, ge=0.1, le=30)
    demo_email: str = "analyst@example.com"
    demo_password: str = Field(default="avenward-demo-only")


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""

    return Settings()
