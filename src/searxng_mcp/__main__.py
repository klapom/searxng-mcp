"""SearXNG MCP Server — dual REST (32700) + MCP Streamable-HTTP (33700) in one process."""

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
from collections.abc import AsyncIterator

import uvicorn
from dotenv import load_dotenv
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from searxng_mcp.server import SearXNGMCP

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("searxng-mcp")


def create_mcp_app(searxng: SearXNGMCP) -> Starlette:
    mcp = searxng.start()
    session_manager = StreamableHTTPSessionManager(app=mcp, stateless=False)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    return Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[Mount("/mcp", app=session_manager.handle_request)],
    )


def create_rest_app(searxng: SearXNGMCP) -> Starlette:
    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "searxng": searxng.searxng_url, "tools": ["web_search", "image_search", "news_search"]})

    async def tools(request: Request) -> JSONResponse:
        return JSONResponse({"tools": ["web_search", "image_search", "news_search"]})

    async def call_tool(request: Request) -> Response:
        tool = request.path_params["tool"]
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"ok": False, "error": "Body must be a JSON object"}, status_code=400)
        try:
            result = await searxng._dispatch(tool, body)
            text = "\n".join(getattr(c, "text", "") for c in result)
            return JSONResponse({"ok": True, "content": [{"type": "text", "text": text}]})
        except Exception as e:
            logger.exception(f"Tool {tool} failed")
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    return Starlette(
        debug=False,
        routes=[
            Route("/", health),
            Route("/health", health),
            Route("/tools", tools),
            Route("/tools/{tool}", call_tool, methods=["POST"]),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SearXNG MCP Server")
    parser.add_argument("--host", default=os.getenv("LISTEN_HOST", os.getenv("HOST", "0.0.0.0")))
    parser.add_argument("--searxng-url", default=os.getenv("SEARXNG_URL", "http://localhost:8888"))
    args = parser.parse_args()

    rest_port = int(os.getenv("LISTEN_PORT", "32700"))
    mcp_port = int(os.getenv("MCP_PORT", "33700"))

    logger.info(f"Starting SearXNG — backend={args.searxng_url} REST={rest_port} MCP={mcp_port}")
    searxng = SearXNGMCP(searxng_url=args.searxng_url)

    rest_app = create_rest_app(searxng)
    mcp_app = create_mcp_app(searxng)

    rest_cfg = uvicorn.Config(rest_app, host=args.host, port=rest_port, log_level="info")
    mcp_cfg = uvicorn.Config(mcp_app, host=args.host, port=mcp_port, log_level="info")

    async def _run() -> None:
        await asyncio.gather(
            uvicorn.Server(rest_cfg).serve(),
            uvicorn.Server(mcp_cfg).serve(),
        )

    asyncio.run(_run())


if __name__ == "__main__":
    main()
