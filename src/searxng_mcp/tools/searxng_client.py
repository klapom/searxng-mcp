"""Thin httpx wrapper around the SearXNG ``/search`` endpoint.

Kept separate so tests can mock via respx without touching tool-handler code.

2026-06-11 — Engine-Rotation + Outgoing-Drossel (Anti-Ban):
Die Default-General-Engines wurden anbieterseitig IP-gesperrt (google
"access denied", ddg/startpage CAPTCHA, brave 429), weil Agent-Turns
Query-Bursts fan-out auf ALLE Engines feuern. Gegenmaßnahmen hier am
einzigen Choke-Point:

* **Rotation:** ``category=general``-Suchen ohne explizites ``engines``-
  Param gehen pro Request nur an EINE Engine-Gruppe (round-robin) statt an
  alle — verteilt die Last pro Anbieter. Liefert die Gruppe 0 Treffer
  (z.B. weil gerade suspendiert), wird einmal ohne ``engines``-Param
  nachgefasst (= alle aktivierten Engines als Fallback).
* **Drossel:** globaler Mindestabstand zwischen Upstream-Requests mit
  Jitter, damit ein 10-Suchen-Turn nicht als Bot-Burst auffällt.

Konfiguration via env (Defaults in Klammern):
``SEARXNG_MCP_ENGINE_GROUPS``  Semikolon-getrennte Gruppen
    ("bing,mojeek;startpage,yahoo;qwant,presearch;duckduckgo,brave");
    leer = Rotation aus.
``SEARXNG_MCP_MIN_INTERVAL``   Mindestabstand in Sekunden (3.0); 0 = aus.
``SEARXNG_MCP_JITTER_MAX``     zusätzlicher Zufalls-Jitter 0..x s (2.0).
"""

from __future__ import annotations

import asyncio
import itertools
import os
import random
import time
from typing import Any

import httpx

from searxng_mcp.config import get_settings

_ENGINE_GROUPS = [
    g.strip()
    for g in os.environ.get(
        "SEARXNG_MCP_ENGINE_GROUPS",
        "bing,mojeek;startpage,yahoo;qwant,presearch;duckduckgo,brave",
    ).split(";")
    if g.strip()
]
_rotation = itertools.cycle(_ENGINE_GROUPS) if _ENGINE_GROUPS else None

_MIN_INTERVAL = float(os.environ.get("SEARXNG_MCP_MIN_INTERVAL", "3.0"))
_JITTER_MAX = float(os.environ.get("SEARXNG_MCP_JITTER_MAX", "2.0"))
_throttle_lock = asyncio.Lock()
_last_request_ts = 0.0


async def _throttle() -> None:
    """Enforce the global min-interval (+ jitter) between upstream requests."""
    global _last_request_ts
    if _MIN_INTERVAL <= 0:
        return
    async with _throttle_lock:
        wait = (
            _last_request_ts
            + _MIN_INTERVAL
            + random.uniform(0.0, _JITTER_MAX)
            - time.monotonic()
        )
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_ts = time.monotonic()


async def _get(params: dict[str, Any]) -> dict[str, Any]:
    base = get_settings().searxng_url.rstrip("/")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{base}/search", params=params)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result


async def search(params: dict[str, Any]) -> dict[str, Any]:
    """Throttled GET to SearXNG with engine rotation for general searches.

    Rotation only applies when the caller did not pin ``engines`` and the
    category is ``general`` (news/images/… have their own engine sets).
    Raises on non-2xx. Returns parsed JSON.
    """
    await _throttle()
    rotate = (
        _rotation is not None
        and "engines" not in params
        and params.get("categories", "general") == "general"
    )
    if not rotate:
        return await _get(params)

    group = next(_rotation)
    result = await _get({**params, "engines": group})
    if result.get("results"):
        return result
    # Gruppe leer/suspendiert → einmal breit nachfassen (alle Engines).
    await _throttle()
    return await _get(params)
