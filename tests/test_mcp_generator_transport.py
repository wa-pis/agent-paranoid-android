from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

import test_data_agent.mcp_generator_transport as transport
import test_data_agent.mcp_trino_transport as shared_transport
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
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


def test_generator_transport_registers_audited_services_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audited: list[tuple[str, str]] = []

    def profile_csv() -> str:
        return "profiled"

    def generate_dataset() -> str:
        return "generated"

    def record_audit(
        service: str,
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        audited.append((service, function.__name__))
        return function

    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    monkeypatch.setattr(transport, "audited_mcp_tool", record_audit)
    services = (profile_csv, generate_dataset)

    mcp = transport.create_generator_mcp(services)

    assert isinstance(mcp, FakeMCP)
    assert mcp.name == "test-data-agent-generator"
    assert [tool.__name__ for tool in mcp.tools] == [
        "profile_csv",
        "generate_dataset",
    ]
    assert audited == [
        ("generator-mcp", "profile_csv"),
        ("generator-mcp", "generate_dataset"),
    ]
    assert mcp.tools[0]() == "profiled"
    assert mcp.tools[1]() == "generated"


def test_generator_transport_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport, "FastMCP", None)

    assert transport.create_generator_mcp(()) is None


def test_generator_transport_uses_shared_bounded_runner() -> None:
    assert transport.run_bounded_generator_mcp is shared_transport.run_bounded_mcp


def test_generator_fastmcp_argument_validation_is_fixed_and_source_free() -> None:
    if transport.FastMCP is None:
        pytest.skip("installed MCP version does not provide FastMCP")

    import anyio
    import mcp.types as types

    source_literal = "synthetic_rejected_argument"
    calls: list[int] = []

    def bounded_tool(limit: int) -> str:
        calls.append(limit)
        return str(limit)

    mcp = transport.create_generator_mcp((bounded_tool,))
    assert mcp is not None
    request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(
            name="bounded_tool",
            arguments={"limit": source_literal},
        ),
    )
    handler = mcp._mcp_server.request_handlers[types.CallToolRequest]

    result = anyio.run(handler, request)
    payload = result.root.model_dump_json()

    assert result.root.isError is True
    assert shared_transport._INVALID_TOOL_ARGUMENTS_MESSAGE in payload
    assert source_literal not in payload
    assert calls == []


@pytest.mark.parametrize(
    ("limits", "params", "dimension"),
    [
        ({"ast_depth": 2}, {"value": [[[1]]]}, QueryWorkDimension.AST_DEPTH),
        ({"ast_nodes": 6}, {"value": [1, 2, 3, 4]}, QueryWorkDimension.AST_NODES),
    ],
)
def test_generator_transport_rejects_structurally_oversized_json_before_parse(
    limits: dict[str, int],
    params: dict[str, Any],
    dimension: QueryWorkDimension,
) -> None:
    work_limits = replace(DEFAULT_QUERY_WORK_LIMITS, **limits)
    raw_payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}
    ).encode()

    def budget_factory(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(work_limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    with pytest.raises(QueryWorkBudgetExceeded) as raised:
        shared_transport._bounded_session_message(raw_payload, budget_factory)

    assert raised.value.dimension is dimension


@pytest.mark.parametrize("method", ["123456789", "\\" * 9])
def test_generator_transport_rejects_oversized_json_scalar_before_parse(
    method: str,
) -> None:
    work_limits = replace(DEFAULT_QUERY_WORK_LIMITS, canonical_argument_bytes=8)
    raw_payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method}).encode()

    def budget_factory(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(work_limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    with pytest.raises(ValueError, match="JSON scalar exceeds structural limit"):
        shared_transport._bounded_session_message(raw_payload, budget_factory)
