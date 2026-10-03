"""Transport registration for generator MCP application services."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from inspect import cleandoc, signature
from typing import Any

from test_data_agent.audit import audited_mcp_tool
from test_data_agent.mcp_trino_transport import (
    FastMCP,
    _create_redacted_fast_mcp,
    run_bounded_mcp,
)


def create_generator_mcp(
    tools: Sequence[Callable[..., Any]],
    *, strict_arguments: bool = False,
) -> Any | None:
    """Register audited generator services without owning their safety policy."""

    if FastMCP is None:
        return None

    argument_names = ({tool.__name__: frozenset(signature(tool).parameters) for tool in tools}
                      if strict_arguments else None)
    mcp = _create_redacted_fast_mcp("test-data-agent-generator", FastMCP,
                                    argument_names=argument_names)
    for tool in tools:
        mcp.tool(description=cleandoc(tool.__doc__ or ""))(
            audited_mcp_tool("generator-mcp", tool))
    return mcp


run_bounded_generator_mcp = run_bounded_mcp
