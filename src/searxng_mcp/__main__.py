"""Stdio entry point — ``python -m searxng_mcp`` or ``searxng-mcp``.

Claude Desktop speaks stdio. This is the *only* surface needed for that
consumer; REST + Streamable-HTTP live in ``http_server.py``.
"""

from __future__ import annotations

from searxng_mcp import __service_name__, __version__
from searxng_mcp.config import get_settings
from searxng_mcp.logging import setup_logging
from searxng_mcp.metrics import init_metrics


def main_stdio() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    init_metrics(__service_name__, __version__)

    # Import *after* logging is configured so FastMCP uses our handlers.
    from searxng_mcp.server import mcp

    mcp.run()  # defaults to stdio transport


if __name__ == "__main__":
    main_stdio()
