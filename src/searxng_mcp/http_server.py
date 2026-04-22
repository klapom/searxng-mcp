"""Dual-surface HTTP entry: REST (32xxx) + MCP Streamable-HTTP (33xxx).

Both surfaces share the same FastMCP instance (``server.mcp``), so a tool
registered via ``@mcp.tool()`` is automatically reachable on all three
surfaces (this module's REST + MCP, and stdio via ``__main__.py``).

Run with:
    uv run searxng-mcp-http
"""

from __future__ import annotations

import asyncio
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from searxng_mcp import __service_name__, __version__
from searxng_mcp.config import get_settings
from searxng_mcp.logging import get_logger, setup_logging
from searxng_mcp.metrics import init_metrics, render_metrics
from searxng_mcp.server import mcp

log = get_logger(__name__)


def _serialize(result: Any) -> dict[str, Any]:
    """Normalize FastMCP call_tool result into plain JSON. Handles (content, structured) tuple."""
    structured: Any = None
    content: Any = result
    if isinstance(result, tuple) and len(result) == 2:
        content, structured = result

    texts: list[str] = []
    try:
        for block in content or []:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(text)
    except TypeError:
        pass

    return {
        "ok": True,
        "content": [{"type": "text", "text": t} for t in texts],
        "structured": structured,
    }


def build_rest_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=f"{__service_name__} REST", version=__version__)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        tools = await mcp.list_tools()
        return {
            "service": __service_name__,
            "version": __version__,
            "status": "ok",
            "tools": [t.name for t in tools],
            "mcpEndpoint": f"http://0.0.0.0:{settings.mcp_port}/mcp",
        }

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content=render_metrics(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    @app.get("/tools")
    async def list_tools() -> dict[str, Any]:
        tools = await mcp.list_tools()
        return {
            "count": len(tools),
            "tools": [
                {
                    "name": t.name,
                    "description": (t.description or "").strip().split("\n", 1)[0],
                    "input_schema": t.inputSchema,
                }
                for t in tools
            ],
        }

    @app.post("/tools/{tool_name}")
    async def call_tool(tool_name: str, request: Request) -> dict[str, Any]:
        try:
            body = await request.json() if await request.body() else {}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}") from e
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Body must be a JSON object.")

        tools = await mcp.list_tools()
        if tool_name not in {t.name for t in tools}:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

        try:
            result = await mcp.call_tool(tool_name, body)
        except Exception as e:
            log.exception("tool_error", tool=tool_name)
            raise HTTPException(status_code=500, detail=str(e)) from e
        return _serialize(result)

    return app


async def _run_both() -> None:
    settings = get_settings()
    rest_app = build_rest_app()
    mcp_app = mcp.streamable_http_app()  # FastMCP 2.x → Starlette app mounted at /mcp

    rest_config = uvicorn.Config(
        rest_app,
        host="0.0.0.0",
        port=settings.listen_port,
        log_config=None,  # structlog handles logs
        access_log=False,
    )
    mcp_config = uvicorn.Config(
        mcp_app,
        host="0.0.0.0",
        port=settings.mcp_port,
        log_config=None,
        access_log=False,
    )

    rest_server = uvicorn.Server(rest_config)
    mcp_server = uvicorn.Server(mcp_config)

    log.info(
        "dual_surface_start",
        service=__service_name__,
        version=__version__,
        rest_port=settings.listen_port,
        mcp_port=settings.mcp_port,
    )

    await asyncio.gather(rest_server.serve(), mcp_server.serve())


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    init_metrics(__service_name__, __version__)
    asyncio.run(_run_both())


if __name__ == "__main__":
    main()
