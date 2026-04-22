"""Factory functions for SearXNG JSON response shapes.

Each function returns a fresh dict to avoid shared-state bugs between tests
(A4 lesson: fixtures as factories, never as module-level constants).
"""

from __future__ import annotations

from typing import Any


def web_result(
    title: str,
    url: str,
    content: str | None = None,
    engines: list[str] | None = None,
    publishedDate: str | None = None,  # noqa: N803 — matches SearXNG JSON key
) -> dict[str, Any]:
    """Build a single web/news result dict."""
    r: dict[str, Any] = {"title": title, "url": url}
    if content is not None:
        r["content"] = content
    if engines is not None:
        r["engines"] = engines
    if publishedDate is not None:
        r["publishedDate"] = publishedDate
    return r


def image_result(
    title: str,
    url: str,
    img_src: str | None = None,
    thumbnail_src: str | None = None,
    resolution: str | None = None,
    source: str | None = None,
    engines: list[str] | None = None,
) -> dict[str, Any]:
    """Build a single image result dict."""
    r: dict[str, Any] = {"title": title, "url": url}
    if img_src is not None:
        r["img_src"] = img_src
    if thumbnail_src is not None:
        r["thumbnail_src"] = thumbnail_src
    if resolution is not None:
        r["resolution"] = resolution
    if source is not None:
        r["source"] = source
    if engines is not None:
        r["engines"] = engines
    return r


def news_result(
    title: str,
    url: str,
    content: str | None = None,
    publishedDate: str | None = None,  # noqa: N803
    engines: list[str] | None = None,
) -> dict[str, Any]:
    """Build a single news result dict."""
    r: dict[str, Any] = {"title": title, "url": url}
    if content is not None:
        r["content"] = content
    if publishedDate is not None:
        r["publishedDate"] = publishedDate
    if engines is not None:
        r["engines"] = engines
    return r


def web_response(
    query: str = "test",
    results: list[dict[str, Any]] | None = None,
    answers: list[str] | None = None,
    infoboxes: list[dict[str, Any]] | None = None,
    suggestions: list[str] | None = None,
    number_of_results: int = 42,
) -> dict[str, Any]:
    """Build a SearXNG web-search JSON response."""
    return {
        "query": query,
        "number_of_results": number_of_results,
        "results": results or [],
        "answers": answers or [],
        "infoboxes": infoboxes or [],
        "suggestions": suggestions or [],
    }


def image_response(
    query: str = "test",
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a SearXNG image-search JSON response."""
    return {
        "query": query,
        "number_of_results": len(results or []),
        "results": results or [],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
    }


def news_response(
    query: str = "test",
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a SearXNG news-search JSON response."""
    return {
        "query": query,
        "number_of_results": len(results or []),
        "results": results or [],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
    }
