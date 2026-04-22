"""Web search tool — delegates to SearXNG ``/search?categories=general``."""

from __future__ import annotations

from typing import Literal

from searxng_mcp.server import mcp
from searxng_mcp.tools.searxng_client import search

Category = Literal["general", "news", "images", "videos", "science", "files", "social media"]
TimeRange = Literal["day", "week", "month", "year"]


@mcp.tool()
async def web_search(
    query: str,
    category: Category = "general",
    language: str = "auto",
    time_range: TimeRange | None = None,
    max_results: int = 10,
) -> str:
    """Search the web via SearXNG (privacy-preserving meta search).

    Returns a Markdown-formatted result list with ranked hits from multiple
    upstream engines, plus any instant-answer infoboxes.
    """
    params: dict[str, str] = {
        "q": query,
        "format": "json",
        "categories": category,
        "language": language,
    }
    if time_range is not None:
        params["time_range"] = time_range

    data = await search(params)
    results = data.get("results", [])[:max_results]

    lines: list[str] = [
        f'# Search: "{data.get("query", query)}"',
        f"~{data.get('number_of_results', 0):,} results\n",
    ]

    if answers := data.get("answers"):
        lines.append("## Instant Answers")
        lines.extend(f"- {a}" for a in answers)
        lines.append("")

    for box in data.get("infoboxes", []):
        lines.append(f"## {box.get('infobox', '')}")
        if content := box.get("content"):
            lines.append(content)
        for u in box.get("urls", []):
            lines.append(f"- [{u.get('title', '')}]({u.get('url', '')})")
        lines.append("")

    lines.append("## Results")
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r.get('title', '')}")
        lines.append(f"**URL:** {r.get('url', '')}")
        if content := r.get("content"):
            lines.append(content)
        if published := r.get("publishedDate"):
            lines.append(f"*Published: {published}*")
        if engines := r.get("engines"):
            lines.append(f"*Sources: {', '.join(engines)}*")
        lines.append("")

    if suggestions := data.get("suggestions", [])[:5]:
        lines.append("## Related searches")
        lines.append(" · ".join(suggestions))

    return "\n".join(lines)
