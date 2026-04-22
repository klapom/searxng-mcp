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

__all__ = ["__service_name__", "__version__", "mcp"]
