"""Settings — extends ``BaseServiceSettings`` from mcp-toolkit-py (ADR-010)."""

from __future__ import annotations

from functools import lru_cache

from mcp_toolkit_py.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    listen_port: int = 32700
    mcp_port: int = 33700

    # Service-specific
    searxng_url: str = "http://localhost:8888"


@lru_cache
def get_settings() -> Settings:
    return Settings()
