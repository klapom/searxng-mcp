"""Image search tool — delegates to SearXNG ``/search?categories=images``."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from searxng_mcp.server import mcp
from searxng_mcp.tools.searxng_client import search

TimeRange = Literal["day", "week", "month", "year"]


@mcp.tool()
async def image_search(
    query: str,
    language: str = "auto",
    time_range: TimeRange | None = None,
    max_results: int = 8,
) -> str:
    """Search for images via SearXNG.

    Returns a Markdown list with thumbnail/image URLs, source hostname and
    resolution per hit.
    """
    params: dict[str, str] = {
        "q": query,
        "format": "json",
        "categories": "images",
        "language": language,
    }
    if time_range is not None:
        params["time_range"] = time_range

    data = await search(params)
    results = data.get("results", [])[:max_results]

    lines: list[str] = [f'# Image Search: "{query}"\n']
    for i, r in enumerate(results, 1):
        url = r.get("url", "")
        source = r.get("source") or urlparse(url).hostname or url
        lines.append(f"### {i}. {r.get('title', '')}")
        lines.append(f"**Source:** {source}")
        lines.append(f"**Page:** {url}")
        if img_src := r.get("img_src"):
            lines.append(f"**Image:** {img_src}")
        if thumb := r.get("thumbnail_src"):
            lines.append(f"**Thumbnail:** {thumb}")
        if resolution := r.get("resolution"):
            lines.append(f"**Resolution:** {resolution}")
        if engines := r.get("engines"):
            lines.append(f"*Engines: {', '.join(engines)}*")
        lines.append("")

    return "\n".join(lines)
