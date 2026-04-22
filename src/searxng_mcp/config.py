"""Settings — pydantic-settings with process-env priority (ADR-010)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    listen_port: int = 32700
    mcp_port: int = 33700
    log_level: Literal["debug", "info", "warning", "error"] = "info"

    searxng_url: str = "http://localhost:8888"


@lru_cache
def get_settings() -> Settings:
    return Settings()
