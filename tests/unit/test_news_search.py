"""Unit tests for news_search tool."""

from __future__ import annotations

import httpx
import pytest
import respx

from searxng_mcp.config import get_settings
from searxng_mcp.tools.news_search import news_search
from tests.fixtures.searxng import news_response, news_result


def _base_url() -> str:
    return get_settings().searxng_url.rstrip("/")


@respx.mock
async def test_news_search_happy_path() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(
            200,
            json=news_response(
                query="AI",
                results=[
                    news_result(
                        title="AI breakthrough",
                        url="https://news.example.com/ai",
                        content="Researchers announced...",
                        publishedDate="2026-04-20T10:00:00Z",
                        engines=["reuters", "ap"],
                    )
                ],
            ),
        )
    )
    out = await news_search("AI")
    assert '# News: "AI"' in out
    assert "### 1. AI breakthrough" in out
    assert "**URL:** https://news.example.com/ai" in out
    assert "**Published:** 2026-04-20T10:00:00Z" in out
    assert "Researchers announced..." in out
    assert "*Sources: reuters, ap*" in out


@respx.mock
async def test_news_search_default_time_range_is_week() -> None:
    route = respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=news_response())
    )
    await news_search("foo")
    assert route.called
    assert route.calls.last.request.url.params["time_range"] == "week"
    assert route.calls.last.request.url.params["categories"] == "news"


@respx.mock
async def test_news_search_custom_time_range() -> None:
    route = respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=news_response())
    )
    await news_search("foo", time_range="day")
    assert route.calls.last.request.url.params["time_range"] == "day"


@respx.mock
async def test_news_search_empty_results() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=news_response(query="zzz"))
    )
    out = await news_search("zzz")
    assert '# News: "zzz"' in out
    assert "###" not in out


@respx.mock
async def test_news_search_upstream_error() -> None:
    respx.get(f"{_base_url()}/search").mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await news_search("boom")


@respx.mock
async def test_news_search_respects_max_results() -> None:
    results = [news_result(f"t{i}", f"https://x/{i}") for i in range(15)]
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=news_response(results=results))
    )
    out = await news_search("x", max_results=2)
    assert "### 1. t0" in out
    assert "### 2. t1" in out
    assert "### 3." not in out
