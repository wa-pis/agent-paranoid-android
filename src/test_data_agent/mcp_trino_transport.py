"""Transport registration for allowlisted Trino MCP services."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[misc, assignment]

from test_data_agent.audit import audited_mcp_tool


def create_trino_mcp(
    tools: Sequence[Callable[..., Any]],
) -> Any | None:
    """Register audited services without owning their SQL safety policy."""

    if FastMCP is None:
        return None

    mcp = FastMCP("test-data-agent-trino")
    for tool in tools:
        mcp.tool()(audited_mcp_tool("trino-mcp", tool))
    return mcp
