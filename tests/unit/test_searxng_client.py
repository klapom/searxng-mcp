"""Unit tests for searxng_client engine rotation + throttle (2026-06-11)."""

from __future__ import annotations

import itertools

import httpx
import pytest
import respx

import searxng_mcp.tools.searxng_client as sc
from searxng_mcp.config import get_settings
from tests.fixtures.searxng import web_response, web_result


def _base_url() -> str:
    return get_settings().searxng_url.rstrip("/")


@pytest.fixture(autouse=True)
def _no_throttle(monkeypatch):
    """Disable the min-interval in unit tests (no real sleeps)."""
    monkeypatch.setattr(sc, "_MIN_INTERVAL", 0.0)


@pytest.fixture()
def _fresh_rotation(monkeypatch):
    groups = ["bing,mojeek", "startpage,yahoo"]
    monkeypatch.setattr(sc, "_ENGINE_GROUPS", groups)
    monkeypatch.setattr(sc, "_rotation", itertools.cycle(groups))
    return groups


def _ok_response(n: int = 1) -> httpx.Response:
    results = [web_result(f"hit {i}", f"https://x{i}.de") for i in range(n)]
    return httpx.Response(200, json=web_response(query="q", results=results))


@respx.mock
async def test_general_search_rotates_engine_groups(_fresh_rotation):
    route = respx.get(f"{_base_url()}/search").mock(return_value=_ok_response())
    await sc.search({"q": "a", "format": "json", "categories": "general"})
    await sc.search({"q": "b", "format": "json", "categories": "general"})
    await sc.search({"q": "c", "format": "json", "categories": "general"})
    engines = [httpx.QueryParams(c.request.url.query).get("engines") for c in route.calls]
    assert engines == ["bing,mojeek", "startpage,yahoo", "bing,mojeek"]


@respx.mock
async def test_zero_results_falls_back_to_all_engines(_fresh_rotation):
    empty = httpx.Response(200, json=web_response(query="q", results=[]))
    route = respx.get(f"{_base_url()}/search").mock(
        side_effect=[empty, _ok_response()]
    )
    out = await sc.search({"q": "a", "format": "json", "categories": "general"})
    assert out["results"], "fallback result expected"
    assert len(route.calls) == 2
    first = httpx.QueryParams(route.calls[0].request.url.query)
    second = httpx.QueryParams(route.calls[1].request.url.query)
    assert first.get("engines") == "bing,mojeek"
    assert second.get("engines") is None  # breiter Fallback ohne Pinning


@respx.mock
async def test_non_general_category_not_rotated(_fresh_rotation):
    route = respx.get(f"{_base_url()}/search").mock(return_value=_ok_response())
    await sc.search({"q": "a", "format": "json", "categories": "news"})
    params = httpx.QueryParams(route.calls[0].request.url.query)
    assert params.get("engines") is None


@respx.mock
async def test_explicit_engines_param_respected(_fresh_rotation):
    route = respx.get(f"{_base_url()}/search").mock(return_value=_ok_response())
    await sc.search(
        {"q": "a", "format": "json", "categories": "general", "engines": "mojeek"}
    )
    params = httpx.QueryParams(route.calls[0].request.url.query)
    assert params.get("engines") == "mojeek"


@respx.mock
async def test_rotation_disabled_when_no_groups(monkeypatch):
    monkeypatch.setattr(sc, "_rotation", None)
    route = respx.get(f"{_base_url()}/search").mock(return_value=_ok_response())
    await sc.search({"q": "a", "format": "json", "categories": "general"})
    params = httpx.QueryParams(route.calls[0].request.url.query)
    assert params.get("engines") is None


async def test_throttle_enforces_min_interval(monkeypatch):
    import time as _time

    monkeypatch.setattr(sc, "_MIN_INTERVAL", 0.05)
    monkeypatch.setattr(sc, "_JITTER_MAX", 0.0)
    monkeypatch.setattr(sc, "_last_request_ts", 0.0)
    t0 = _time.monotonic()
    await sc._throttle()
    await sc._throttle()
    await sc._throttle()
    assert _time.monotonic() - t0 >= 0.10  # 2 Wartefenster à 50 ms
