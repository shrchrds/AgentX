"""Application settings loaded from environment variables.

Uses pydantic-settings to validate and parse configuration.
Never hardcode secrets — all sensitive values come from .env or env vars.
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AgentX application.

    All fields are populated from environment variables or a .env file.
    Required fields (no default) will cause a startup error if missing,
    ensuring secrets are never accidentally omitted.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # --- Memory ---
    memory_backend: Literal["memory", "faiss", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379/0"

    # --- API Security ---
    api_secret_key: str = ""
    rate_limit_per_minute: int = 60

    # --- Logging ---
    log_level: str = "INFO"


# Singleton instance used throughout the application.
settings = Settings()
