from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

import test_data_agent.mcp_trino_server as server
import test_data_agent.mcp_trino_transport as transport


DEFAULT_TRINO_TOOL_NAMES = (
    "list_catalogs",
    "list_schemas",
    "list_tables",
    "describe_table",
    "profile_table",
    "profile_column",
    "profile_table_safe",
    "profile_foreign_key",
    "profile_temporal_ordering",
    "profile_formula_rule",
    "profile_conditional_required",
    "profile_conditional_allowed_values",
    "profile_aggregate_mapping",
)


class FakeMCP:
    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: list[Callable[..., Any]] = []

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def register(function: Callable[..., Any]) -> Callable[..., Any]:
            self.tools.append(function)
            return function

        return register


def test_trino_transport_registers_audited_services_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audited: list[tuple[str, str]] = []

    def list_catalogs() -> list[str]:
        return ["catalog"]

    def describe_table() -> list[dict[str, str]]:
        return []

    def record_audit(
        service: str,
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        audited.append((service, function.__name__))
        return function

    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    monkeypatch.setattr(transport, "audited_mcp_tool", record_audit)

    mcp = transport.create_trino_mcp((list_catalogs, describe_table))

    assert isinstance(mcp, FakeMCP)
    assert mcp.name == "test-data-agent-trino"
    assert [tool.__name__ for tool in mcp.tools] == [
        "list_catalogs",
        "describe_table",
    ]
    assert audited == [
        ("trino-mcp", "list_catalogs"),
        ("trino-mcp", "describe_table"),
    ]
    assert mcp.tools[0]() == ["catalog"]
    assert mcp.tools[1]() == []


def test_transport_registers_complete_default_tool_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audited: list[tuple[str, str]] = []

    def record_audit(
        service: str,
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        audited.append((service, function.__name__))
        return function

    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    monkeypatch.setattr(transport, "audited_mcp_tool", record_audit)
    tools = tuple(server.trino_mcp_tools())

    mcp = transport.create_trino_mcp(tools)

    assert tuple(tool.__name__ for tool in tools) == DEFAULT_TRINO_TOOL_NAMES
    assert isinstance(mcp, FakeMCP)
    assert tuple(tool.__name__ for tool in mcp.tools) == DEFAULT_TRINO_TOOL_NAMES
    assert audited == [
        ("trino-mcp", name) for name in DEFAULT_TRINO_TOOL_NAMES
    ]


def test_trino_transport_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport, "FastMCP", None)

    assert transport.create_trino_mcp(()) is None
