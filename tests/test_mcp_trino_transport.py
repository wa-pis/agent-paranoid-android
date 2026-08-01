from __future__ import annotations

import inspect
import json
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

DEFAULT_ARGUMENT_VALUES: dict[str, Any] = {
    "catalog": "analytics",
    "schema": "safe_schema",
    "table": "synthetic_orders",
    "column": "amount",
    "parent_table": "synthetic_customers",
    "parent_field": "customer_id",
    "child_table": "synthetic_orders",
    "child_field": "customer_id",
    "start_field": "created_at",
    "end_field": "fulfilled_at",
    "target_field": "total",
    "expression": "subtotal + tax",
    "condition_field": "status",
    "condition_equals": "transport-source-literal-condition",
    "required_field": "fulfilled_at",
    "value_field": "status",
    "allowed_values": ["transport-source-literal-allowed"],
    "parent_key": "customer_id",
    "parent_value_field": "lifetime_value",
    "child_key": "customer_id",
    "child_value_field": "amount",
}


class RecordingProfiler:
    def __init__(self, failure_message: str | None = None) -> None:
        self.calls: list[str] = []
        self.failure_message = failure_message

    def __getattr__(self, name: str) -> Any:
        def invoke(*args: Any, **kwargs: Any) -> Any:
            self.calls.append(name)
            if self.failure_message is not None:
                raise ValueError(self.failure_message)
            if name == "list_catalogs":
                return ["analytics"]
            if name == "list_schemas":
                return ["safe_schema"]
            if name == "list_tables":
                return ["synthetic_orders"]
            if name == "describe_table":
                return [{"name": "amount", "data_type": "double"}]
            return {"tool": name, "counts": {"checked": 1, "failed": 0}}

        return invoke


def required_tool_arguments(tool: Callable[..., Any]) -> dict[str, Any]:
    return {
        parameter.name: DEFAULT_ARGUMENT_VALUES[parameter.name]
        for parameter in inspect.signature(tool).parameters.values()
        if parameter.default is inspect.Parameter.empty
    }


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


def test_transport_completes_default_tool_success_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler()
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_LOG", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.setattr(server, "_trino_profiler", lambda: profiler)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_tools()))

    assert isinstance(mcp, FakeMCP)
    outputs = {
        tool.__name__: tool(**required_tool_arguments(tool))
        for tool in mcp.tools
    }

    assert tuple(outputs) == DEFAULT_TRINO_TOOL_NAMES
    assert profiler.calls == list(DEFAULT_TRINO_TOOL_NAMES)
    serialized = json.dumps(outputs, sort_keys=True)
    assert "transport-source-literal-condition" not in serialized
    assert "transport-source-literal-allowed" not in serialized


def test_transport_validation_errors_are_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(failure_message="request failed validation")
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_LOG", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.setattr(server, "_trino_profiler", lambda: profiler)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_tools()))

    assert isinstance(mcp, FakeMCP)
    errors: dict[str, dict[str, str]] = {}
    for tool in mcp.tools:
        with pytest.raises(ValueError) as error_info:
            tool(**required_tool_arguments(tool))
        errors[tool.__name__] = {
            "type": type(error_info.value).__name__,
            "message": str(error_info.value),
        }

    assert tuple(errors) == DEFAULT_TRINO_TOOL_NAMES
    assert profiler.calls == list(DEFAULT_TRINO_TOOL_NAMES)
    serialized = json.dumps(errors, sort_keys=True)
    assert "transport-source-literal-condition" not in serialized
    assert "transport-source-literal-allowed" not in serialized


def test_trino_transport_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport, "FastMCP", None)

    assert transport.create_trino_mcp(()) is None
