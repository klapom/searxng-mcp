"""Unit tests for web_search tool."""

from __future__ import annotations

import httpx
import pytest
import respx

from searxng_mcp.config import get_settings
from searxng_mcp.tools.web_search import web_search
from tests.fixtures.searxng import web_response, web_result


def _base_url() -> str:
    return get_settings().searxng_url.rstrip("/")


@respx.mock
async def test_web_search_returns_results() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(
            200,
            json=web_response(
                query="hamburg",
                results=[
                    web_result(
                        "Hamburg",
                        "https://hh.de",
                        content="nice city",
                        engines=["duckduckgo", "brave"],
                        publishedDate="2026-04-01",
                    )
                ],
                number_of_results=1234,
            ),
        )
    )
    out = await web_search("hamburg")
    assert '# Search: "hamburg"' in out
    assert "~1,234 results" in out
    assert "### 1. Hamburg" in out
    assert "**URL:** https://hh.de" in out
    assert "nice city" in out
    assert "*Published: 2026-04-01*" in out
    assert "*Sources: duckduckgo, brave*" in out


@respx.mock
async def test_web_search_with_answers_infoboxes_suggestions() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(
            200,
            json=web_response(
                query="python",
                answers=["Python is a programming language"],
                infoboxes=[
                    {
                        "infobox": "Python",
                        "content": "High-level language",
                        "urls": [{"title": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Python"}],
                    }
                ],
                suggestions=["python tutorial", "python download", "python docs"],
                results=[web_result("Python.org", "https://python.org")],
            ),
        )
    )
    out = await web_search("python")
    assert "## Instant Answers" in out
    assert "- Python is a programming language" in out
    assert "## Python" in out
    assert "High-level language" in out
    assert "- [Wikipedia](https://en.wikipedia.org/wiki/Python)" in out
    assert "## Related searches" in out
    assert "python tutorial · python download · python docs" in out


@respx.mock
async def test_web_search_empty_results() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=web_response(query="zzz", number_of_results=0))
    )
    out = await web_search("zzz")
    assert '# Search: "zzz"' in out
    assert "~0 results" in out
    assert "## Results" in out


@respx.mock
async def test_web_search_time_range_passed_through() -> None:
    route = respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=web_response())
    )
    await web_search("foo", time_range="day")
    assert route.called
    assert route.calls.last.request.url.params["time_range"] == "day"


@respx.mock
async def test_web_search_upstream_error() -> None:
    respx.get(f"{_base_url()}/search").mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await web_search("boom")


@respx.mock
async def test_web_search_respects_max_results() -> None:
    results = [web_result(f"t{i}", f"https://x/{i}") for i in range(20)]
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=web_response(results=results))
    )
    out = await web_search("x", max_results=3)
    assert "### 1. t0" in out
    assert "### 3. t2" in out
    assert "### 4." not in out
