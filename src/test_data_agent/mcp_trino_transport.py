"""Transport registration for allowlisted Trino MCP services."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[misc, assignment]

from test_data_agent.audit import audited_mcp_tool
from test_data_agent.trino_work_budget import (
    QueryWorkLimits,
    with_query_work_budget,
)


DEFAULT_QUERY_WORK_LIMITS = QueryWorkLimits(
    raw_transport_payload_bytes=1024 * 1024,
    canonical_argument_bytes=256 * 1024,
    sql_formula_chars=100_000,
    ast_nodes=10_000,
    ast_depth=100,
    projected_columns=1_000,
    statements=2_048,
    response_bytes=4 * 1024 * 1024,
)


def create_trino_mcp(
    tools: Sequence[Callable[..., Any]],
    *,
    work_limits: QueryWorkLimits = DEFAULT_QUERY_WORK_LIMITS,
) -> Any | None:
    """Register audited services without owning their SQL safety policy."""

    if FastMCP is None:
        return None

    mcp = FastMCP("test-data-agent-trino")
    for tool in tools:
        budgeted_tool = with_query_work_budget(tool, work_limits)
        mcp.tool()(audited_mcp_tool("trino-mcp", budgeted_tool))
    return mcp
