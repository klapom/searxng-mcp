---
name: searxng-mcp
description: Privacy-preserving web/image/news search via SearXNG meta-engine (aggregates results from Google, DuckDuckGo, Bing, etc). Three tools exposed on REST + MCP + stdio. Use when asked to search the web/images/news without tracking.
---

# searxng-mcp

**Version:** 0.4.0 · **Ports:** 32700 REST / 33700 MCP · **Host:** `mcp-searxng.pommerconsulting.de` (CF-Access-Token `searxng-token`)

## Surfaces

- **REST:** `POST http://<host>:32700/tools/<name>` (JSON body) · `GET /tools` · `GET /health` · `GET /metrics`
- **MCP Streamable-HTTP:** `http://<host>:33700/mcp`
- **stdio:** `uv run searxng-mcp` (Claude Desktop)

## Tools

| Name | Args (required) | Args (optional) |
|---|---|---|
| `web_search` | `query` | `category` (general/news/images/videos/science/files/social media), `language`, `time_range` (day/week/month/year), `max_results` (1-20, default 10) |
| `image_search` | `query` | `language`, `time_range`, `max_results` (default 8) |
| `news_search` | `query` | `language`, `time_range` (default week), `max_results` (default 10) |

## Auth

CF-Access-Service-Token extern. LAN: unprotected (SearXNG has no rate-limit model, just Spark's local capacity).

## Beispiele

```bash
# Web search
curl -X POST http://localhost:32700/tools/web_search \
  -H 'content-type: application/json' \
  -d '{"query":"rust async runtime","max_results":5}'

# News (last week default)
curl -X POST http://localhost:32700/tools/news_search \
  -H 'content-type: application/json' \
  -d '{"query":"ai regulation","language":"en"}'

# Images
curl -X POST http://localhost:32700/tools/image_search \
  -H 'content-type: application/json' \
  -d '{"query":"hamburg harbour","max_results":3}'
```

## Backend

Upstream SearXNG instance runs on `localhost:8888` (systemd unit `searxng.service`). If SearXNG is down, all three tools return 500.
