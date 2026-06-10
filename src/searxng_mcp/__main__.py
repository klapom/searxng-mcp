"""Stdio entry point — ``python -m searxng_mcp`` or ``searxng-mcp``.

Thin wrapper over ``mcp_toolkit_py.stdio.run_stdio``.
"""

from __future__ import annotations

from mcp_toolkit_py.stdio import run_stdio

from searxng_mcp import __service_name__, __version__
from searxng_mcp.config import get_settings
from searxng_mcp.server import install_hints, mcp


def main_stdio() -> None:
    settings = get_settings()
    install_hints()
    run_stdio(
        mcp,
        service_name=__service_name__,
        version=__version__,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main_stdio()
