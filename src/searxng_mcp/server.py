"""SearXNG MCP Server — Tool definitions."""

import logging
from typing import Any

import httpx
import mcp.types as types
from mcp.server.lowlevel import Server

logger = logging.getLogger(__name__)

CATEGORIES = ["general", "news", "images", "videos", "science", "files", "social media"]
TIME_RANGES = ["day", "week", "month", "year"]


def _ok(text: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=text)]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Error: {msg}")]


class SearXNGMCP:
    def __init__(self, searxng_url: str):
        self.searxng_url = searxng_url.rstrip("/")
        self.mcp_server = Server("searxng-mcp")
        self._register_handlers()

    def start(self) -> Server:
        return self.mcp_server

    def _register_handlers(self) -> None:
        mcp = self.mcp_server

        @mcp.list_tools()
        async def list_tools() -> list[types.Tool]:
            return TOOL_DEFINITIONS

        @mcp.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            try:
                return await self._dispatch(name, arguments)
            except Exception as e:
                logger.exception(f"Tool '{name}' failed: {e}")
                return _err(str(e))

    async def _search(self, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.searxng_url}/search", params=params)
            resp.raise_for_status()
            return resp.json()

    async def _dispatch(self, name: str, args: dict) -> list[types.TextContent]:
        if name == "web_search":
            return await self._tool_web_search(args)
        elif name == "image_search":
            return await self._tool_image_search(args)
        elif name == "news_search":
            return await self._tool_news_search(args)
        return _err(f"Unknown tool: {name}")

    async def _tool_web_search(self, args: dict) -> list[types.TextContent]:
        params = {
            "q": args["query"],
            "format": "json",
            "categories": args.get("category", "general"),
            "language": args.get("language", "auto"),
        }
        if tr := args.get("time_range"):
            params["time_range"] = tr

        data = await self._search(params)
        max_results = args.get("max_results", 10)
        results = data.get("results", [])[:max_results]

        lines = [f'# Search: "{data.get("query", args["query"])}"',
                 f'~{data.get("number_of_results", 0):,} results\n']

        if answers := data.get("answers"):
            lines += ["## Instant Answers"] + [f"- {a}" for a in answers] + [""]

        for box in data.get("infoboxes", []):
            lines += [f'## {box["infobox"]}', box.get("content", "")]
            for u in box.get("urls", []):
                lines.append(f'- [{u["title"]}]({u["url"]})')
            lines.append("")

        lines.append("## Results")
        for i, r in enumerate(results, 1):
            lines += [f'### {i}. {r["title"]}', f'**URL:** {r["url"]}']
            if r.get("content"):
                lines.append(r["content"])
            if r.get("publishedDate"):
                lines.append(f'*Published: {r["publishedDate"]}*')
            if r.get("engines"):
                lines.append(f'*Sources: {", ".join(r["engines"])}*')
            lines.append("")

        if suggestions := data.get("suggestions", [])[:5]:
            lines += ["## Related searches", " · ".join(suggestions)]

        return _ok("\n".join(lines))

    async def _tool_image_search(self, args: dict) -> list[types.TextContent]:
        params = {
            "q": args["query"],
            "format": "json",
            "categories": "images",
            "language": args.get("language", "auto"),
        }
        if tr := args.get("time_range"):
            params["time_range"] = tr

        data = await self._search(params)
        results = data.get("results", [])[:args.get("max_results", 8)]

        lines = [f'# Image Search: "{args["query"]}"\n']
        for i, r in enumerate(results, 1):
            from urllib.parse import urlparse
            source = r.get("source") or urlparse(r["url"]).hostname or r["url"]
            lines += [f'### {i}. {r["title"]}', f'**Source:** {source}', f'**Page:** {r["url"]}']
            if r.get("img_src"):
                lines.append(f'**Image:** {r["img_src"]}')
            if r.get("thumbnail_src"):
                lines.append(f'**Thumbnail:** {r["thumbnail_src"]}')
            if r.get("resolution"):
                lines.append(f'**Resolution:** {r["resolution"]}')
            if r.get("engines"):
                lines.append(f'*Engines: {", ".join(r["engines"])}*')
            lines.append("")

        return _ok("\n".join(lines))

    async def _tool_news_search(self, args: dict) -> list[types.TextContent]:
        params = {
            "q": args["query"],
            "format": "json",
            "categories": "news",
            "language": args.get("language", "auto"),
            "time_range": args.get("time_range", "week"),
        }

        data = await self._search(params)
        results = data.get("results", [])[:args.get("max_results", 10)]

        lines = [f'# News: "{args["query"]}"\n']
        for i, r in enumerate(results, 1):
            lines += [f'### {i}. {r["title"]}', f'**URL:** {r["url"]}']
            if r.get("publishedDate"):
                lines.append(f'**Published:** {r["publishedDate"]}')
            if r.get("content"):
                lines.append(r["content"])
            if r.get("engines"):
                lines.append(f'*Sources: {", ".join(r["engines"])}*')
            lines.append("")

        return _ok("\n".join(lines))


TOOL_DEFINITIONS: list[types.Tool] = [
    types.Tool(
        name="web_search",
        description=(
            "Search the web via SearXNG (privacy-preserving meta search engine). "
            "Returns ranked results from multiple search engines."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "category": {
                    "type": "string",
                    "enum": CATEGORIES,
                    "default": "general",
                    "description": "Search category",
                },
                "language": {
                    "type": "string",
                    "default": "auto",
                    "description": "Result language (auto, de, en, fr, ...)",
                },
                "time_range": {
                    "type": "string",
                    "enum": TIME_RANGES,
                    "description": "Limit results to time range",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    ),
    types.Tool(
        name="image_search",
        description="Search for images via SearXNG. Returns image URLs, thumbnails, and metadata.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string", "default": "auto"},
                "time_range": {"type": "string", "enum": TIME_RANGES},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
            },
            "required": ["query"],
        },
    ),
    types.Tool(
        name="news_search",
        description="Search for recent news articles via SearXNG.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string", "default": "auto"},
                "time_range": {"type": "string", "enum": TIME_RANGES, "default": "week"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
            },
            "required": ["query"],
        },
    ),
]
