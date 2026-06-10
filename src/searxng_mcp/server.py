"""FastMCP server instance + tool registration.

``mcp`` is the single FastMCP instance shared across all tool modules and
both surfaces (stdio + streamable-HTTP). Tool modules must be imported
*after* ``mcp`` is defined so their ``@mcp.tool()`` decorators run against
this instance.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from searxng_mcp import __service_name__, __version__

mcp = FastMCP(__service_name__)

# Turn off DNS-rebinding protection: required whenever Host header is not
# "localhost" (typical behind CF-Tunnel). See PORT_REGISTRY.md gotcha.
mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)

# Tool modules — imports trigger @mcp.tool() registration.
# Keep imports at the bottom to avoid circular-import issues.
from searxng_mcp.tools import (  # noqa: E402, F401
    image_search,
    news_search,
    web_search,
)


# Sprint 16.7 — Follow-up hints. Opt-in via MCP_FOLLOWUP_HINTS_ENABLED.
# Lazy install: called by entry points after full server import (avoids
# partial-import crashes during test collection — see ot-knowledge Sprint 15.8).
def install_hints() -> None:
    """Wire follow-up hints into the FastMCP server. Idempotent."""
    from pathlib import Path

    from mcp_toolkit_py.hints import install_followup_hints

    rules_path = Path(__file__).parent / "hints" / "rules.yaml"
    registered = set(mcp._tool_manager._tools)
    known_public = {t for t in registered if not t.startswith("internal_")}
    install_followup_hints(mcp, rules_path=rules_path, known_tools=known_public)


__all__ = ["__service_name__", "__version__", "install_hints", "mcp"]
