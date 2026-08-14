"""Transport registration for generator MCP application services."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[misc, assignment]

from test_data_agent.audit import audited_mcp_tool
from test_data_agent.mcp_trino_transport import (
    _create_redacted_fast_mcp,
    run_bounded_mcp,
)


def create_generator_mcp(
    tools: Sequence[Callable[..., Any]],
) -> Any | None:
    """Register audited generator services without owning their safety policy."""

    if FastMCP is None:
        return None

    mcp = _create_redacted_fast_mcp("test-data-agent-generator", FastMCP)
    for tool in tools:
        mcp.tool()(audited_mcp_tool("generator-mcp", tool))
    return mcp


run_bounded_generator_mcp = run_bounded_mcp
