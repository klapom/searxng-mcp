"""Drift-protection test for the bundled hints rules.yaml (Sprint 16.7).

searxng-mcp registers tools via ``@mcp.tool()`` (no explicit ``name=``),
so we use the runtime FastMCP registry rather than source scanning to
discover the live tool set.
"""

from __future__ import annotations

from pathlib import Path

_PKG = "searxng_mcp"
_RULES_PATH = Path(__file__).resolve().parents[2] / "src" / _PKG / "hints" / "rules.yaml"


def _registered_public_tools() -> set[str]:
    """Load the server module and read the live tool registry."""
    from searxng_mcp.server import mcp

    return {name for name in mcp._tool_manager._tools if not name.startswith("internal_")}


def test_bundled_rules_yaml_loads_against_registry():
    """The shipped rules.yaml validates without ValueError against the
    actually-registered public-tool set."""
    from mcp_toolkit_py.hints import load_rules_for_known_tools

    known = _registered_public_tools()
    assert known, "no tools found on the FastMCP registry — import broken?"

    rs = load_rules_for_known_tools(_RULES_PATH, known_tools=known)
    assert rs.version == 1
    assert len(rs.tools) >= 1


def test_every_rules_yaml_target_is_registered():
    """Every source-tool key and every hint target in rules.yaml must be
    a tool the server actually serves."""
    import yaml

    registered = _registered_public_tools()
    data = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))

    referenced: set[str] = set()
    for src_tool, body in (data.get("tools") or {}).items():
        referenced.add(src_tool)
        for hint in body.get("hints", []):
            referenced.add(hint["tool"])

    unknown = referenced - registered
    assert not unknown, (
        f"rules.yaml references tools that aren't registered on the server: {unknown}"
    )
