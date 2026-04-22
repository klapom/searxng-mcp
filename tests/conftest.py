"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from searxng_mcp.config import get_settings
from searxng_mcp.logging import setup_logging


@pytest.fixture(autouse=True, scope="session")
def _silent_logs() -> None:
    """Avoid structlog printing to stdout during tests (pollutes captured output)."""
    setup_logging(level="error")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear lru_cache on get_settings so env-changes between tests take effect."""
    get_settings.cache_clear()
