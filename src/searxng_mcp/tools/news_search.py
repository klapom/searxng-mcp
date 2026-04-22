"""News search tool — delegates to SearXNG ``/search?categories=news``."""

from __future__ import annotations

from typing import Literal

from searxng_mcp.server import mcp
from searxng_mcp.tools.searxng_client import search

TimeRange = Literal["day", "week", "month", "year"]


@mcp.tool()
async def news_search(
    query: str,
    language: str = "auto",
    time_range: TimeRange = "week",
    max_results: int = 10,
) -> str:
    """Search recent news articles via SearXNG.

    Returns a Markdown list with title, URL, published date, snippet content
    and source engines per hit.
    """
    params: dict[str, str] = {
        "q": query,
        "format": "json",
        "categories": "news",
        "language": language,
        "time_range": time_range,
    }

    data = await search(params)
    results = data.get("results", [])[:max_results]

    lines: list[str] = [f'# News: "{query}"\n']
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r.get('title', '')}")
        lines.append(f"**URL:** {r.get('url', '')}")
        if published := r.get("publishedDate"):
            lines.append(f"**Published:** {published}")
        if content := r.get("content"):
            lines.append(content)
        if engines := r.get("engines"):
            lines.append(f"*Sources: {', '.join(engines)}*")
        lines.append("")

    return "\n".join(lines)
