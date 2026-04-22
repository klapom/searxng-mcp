"""Thin httpx wrapper around the SearXNG ``/search`` endpoint.

Kept separate so tests can mock via respx without touching tool-handler code.
"""

from __future__ import annotations

from typing import Any

import httpx

from searxng_mcp.config import get_settings


async def search(params: dict[str, Any]) -> dict[str, Any]:
    """POST-agnostic GET to SearXNG. Raises on non-2xx. Returns parsed JSON."""
    base = get_settings().searxng_url.rstrip("/")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{base}/search", params=params)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result
