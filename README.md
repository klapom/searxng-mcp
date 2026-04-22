# searxng-mcp

MCP Server for [SearXNG](https://github.com/searxng/searxng) — privacy-preserving meta-search wrapper. Exposes `web_search`, `image_search`, `news_search` on three surfaces (REST + MCP Streamable-HTTP + stdio).

**Stack:** Python 3.12 · uv · FastMCP · FastAPI · structlog · pytest+respx
**Ports:** 32700 REST · 33700 MCP (per `PORT_REGISTRY.md`)

## Quickstart

```bash
uv sync --dev
cp .env.example .env
# set SEARXNG_URL=http://localhost:8888 (or external SearXNG host)
uv run searxng-mcp-http          # dual-surface
# or
uv run searxng-mcp               # stdio (Claude Desktop)
```

Health: `curl http://localhost:32700/health`

## Dev

```bash
uv run pytest                    # coverage gate on src/searxng_mcp/tools/
uv run ruff check .
uv run mypy src
```

## Deploy (systemd user-unit)

```bash
cp systemd/searxng-mcp.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now searxng-mcp.service
```

## Tools

| Name | Beschreibung |
|---|---|
| `web_search` | SearXNG `/search?categories=general` — ranked hits + infoboxes + suggestions |
| `image_search` | SearXNG `/search?categories=images` — image URLs + thumbnails + resolution |
| `news_search` | SearXNG `/search?categories=news` — recent news articles |

## Layout

```
src/searxng_mcp/
├── __init__.py           # version + service name
├── __main__.py           # stdio entry
├── http_server.py        # dual-surface (REST + MCP Streamable-HTTP)
├── server.py             # FastMCP instance + tool imports
├── config.py             # pydantic-settings
├── logging.py            # structlog + PII-scrubber
├── metrics.py            # prometheus-client
└── tools/
    ├── searxng_client.py # shared httpx wrapper
    ├── web_search.py
    ├── image_search.py
    └── news_search.py
```

## Related

- `mcp-platform/docs/adr/ADR-005-surfaces.md` — dual-surface contract
- `mcp-platform/docs/inventory/PORT_REGISTRY.md` — port reservation + gotchas
