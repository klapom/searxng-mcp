"""Unit tests for image_search tool."""

from __future__ import annotations

import httpx
import pytest
import respx

from searxng_mcp.config import get_settings
from searxng_mcp.tools.image_search import image_search
from tests.fixtures.searxng import image_response, image_result


def _base_url() -> str:
    return get_settings().searxng_url.rstrip("/")


@respx.mock
async def test_image_search_happy_path() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(
            200,
            json=image_response(
                query="cats",
                results=[
                    image_result(
                        title="Cute Cat",
                        url="https://example.com/cat-page",
                        img_src="https://example.com/cat.jpg",
                        thumbnail_src="https://example.com/cat_thumb.jpg",
                        resolution="1920x1080",
                        source="example.com",
                        engines=["bing images", "duckduckgo images"],
                    )
                ],
            ),
        )
    )
    out = await image_search("cats")
    assert '# Image Search: "cats"' in out
    assert "### 1. Cute Cat" in out
    assert "**Source:** example.com" in out
    assert "**Page:** https://example.com/cat-page" in out
    assert "**Image:** https://example.com/cat.jpg" in out
    assert "**Thumbnail:** https://example.com/cat_thumb.jpg" in out
    assert "**Resolution:** 1920x1080" in out
    assert "*Engines: bing images, duckduckgo images*" in out


@respx.mock
async def test_image_search_source_fallback_from_hostname() -> None:
    """When `source` missing, urlparse hostname is used."""
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(
            200,
            json=image_response(
                results=[
                    image_result(
                        title="Pic",
                        url="https://cdn.images.example.net/path/img.html",
                        img_src="https://cdn.images.example.net/path/img.jpg",
                    )
                ],
            ),
        )
    )
    out = await image_search("pic")
    assert "**Source:** cdn.images.example.net" in out


@respx.mock
async def test_image_search_empty_results() -> None:
    respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=image_response(query="zzz"))
    )
    out = await image_search("zzz")
    assert '# Image Search: "zzz"' in out
    assert "###" not in out


@respx.mock
async def test_image_search_time_range_passed_through() -> None:
    route = respx.get(f"{_base_url()}/search").mock(
        return_value=httpx.Response(200, json=image_response())
    )
    await image_search("foo", time_range="month")
    assert route.called
    assert route.calls.last.request.url.params["time_range"] == "month"
    assert route.calls.last.request.url.params["categories"] == "images"


@respx.mock
async def test_image_search_upstream_error() -> None:
    respx.get(f"{_base_url()}/search").mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await image_search("boom")
