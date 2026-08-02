from __future__ import annotations

import base64
import io
import inspect
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import test_data_agent.mcp_trino_server as server
import test_data_agent.mcp_trino_transport as transport
from test_data_agent.audit import (
    AUDIT_HMAC_KEY_ENV,
    AUDIT_LOG_ENV,
    verify_audit_log,
)
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    MIN_TRANSPORT_RESPONSE_BYTES,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    canonical_argument_size,
    with_query_work_budget,
)
from tests.trino_source_literals import (
    SOURCE_ROWS,
    assert_source_literals_absent,
)


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
    def __init__(
        self,
        failure_message: str | None = None,
        failure_type: type[Exception] = ValueError,
        nested: bool = False,
        source_rows: tuple[dict[str, object], ...] = SOURCE_ROWS,
    ) -> None:
        self.calls: list[str] = []
        self.failure_message = failure_message
        self.failure_type = failure_type
        self.nested = nested
        self.source_count = len(source_rows)

    def __getattr__(self, name: str) -> Any:
        def invoke(*args: Any, **kwargs: Any) -> Any:
            self.calls.append(name)
            if self.failure_message is not None:
                raise self.failure_type(self.failure_message)
            if name == "list_catalogs":
                return ["analytics"]
            if name == "list_schemas":
                return ["safe_schema"]
            if name == "list_tables":
                return ["synthetic_orders"]
            if name == "describe_table":
                if self.nested:
                    return [
                        {
                            "name": "amount",
                            "data_type": "double",
                            "metadata": {"nullable": True},
                        }
                    ]
                return [{"name": "amount", "data_type": "double"}]
            if self.nested:
                return {
                    "tool": name,
                    "summary": {
                        "counts": {
                            "checked": self.source_count,
                            "failed": 0,
                        },
                        "columns": [
                            {
                                "name": "synthetic_metric",
                                "metrics": {"null_ratio": 0.0},
                            }
                        ],
                    },
                }
            return {
                "tool": name,
                "counts": {"checked": self.source_count, "failed": 0},
            }

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


class RecordingStdout:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []
        self.flush_count = 0

    async def write(self, payload: bytes) -> None:
        self.payloads.append(payload)

    async def flush(self) -> None:
        self.flush_count += 1


def test_raw_transport_budget_is_charged_before_json_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed: list[bytes] = []
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, raw_transport_payload_bytes=5)

    def parse_payload(payload: bytes) -> Any:
        parsed.append(payload)
        raise AssertionError("oversized payload must not be parsed")

    monkeypatch.setattr(
        "mcp.types.JSONRPCMessage.model_validate_json",
        parse_payload,
    )

    def create_budget(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    with pytest.raises(QueryWorkBudgetExceeded, match="raw transport payload bytes"):
        transport._bounded_session_message(b"123456", create_budget)

    assert parsed == []


def test_raw_transport_budget_is_attached_to_valid_request() -> None:
    pytest.importorskip("mcp.shared.message")
    payload = b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        raw_transport_payload_bytes=len(payload),
    )

    def create_budget(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    session_message = transport._bounded_session_message(payload, create_budget)
    budget = session_message.metadata.request_context

    assert isinstance(budget, QueryWorkBudget)
    assert budget.snapshot().raw_transport_payload_bytes == len(payload)


@pytest.mark.parametrize(
    "response_json",
    [
        (
            '{"jsonrpc":"2.0","id":"request-1",'
            '"result":{"nested":{"escaped":"line\\nvalue","unicode":"é"}}}'
        ),
        (
            '{"jsonrpc":"2.0","id":"request-1",'
            '"error":{"code":-32603,"message":"bounded error",'
            '"data":{"retryable":false}}}'
        ),
    ],
    ids=("result", "error"),
)
def test_transport_response_budget_counts_final_jsonrpc_and_framing(
    response_json: str,
) -> None:
    import anyio
    import mcp.types as types

    limits = replace(DEFAULT_QUERY_WORK_LIMITS, transport_response_bytes=512)
    budget = QueryWorkBudget(limits)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            '{"jsonrpc":"2.0","id":"request-1","method":"ping"}'
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(response_json),
        metadata=None,
    )
    expected = response.message.model_dump_json(
        by_alias=True,
        exclude_none=True,
    ).encode("utf-8") + b"\n"
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert stdout.payloads == [expected]
    assert stdout.flush_count == 1
    assert budget.snapshot().transport_response_bytes == len(expected)


def test_transport_budget_counts_nested_metadata_and_escaping_expansion() -> None:
    import anyio
    import mcp.types as types

    escaped_value = 'line\n"quoted"\\path\tunicodé' * 16
    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "nested-metadata",
                    "result": {
                        "metadata": {
                            "columns": [
                                {
                                    "name": "synthetic_note",
                                    "labels": [escaped_value],
                                }
                            ]
                        }
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=None,
    )
    expected = response.message.model_dump_json(
        by_alias=True,
        exclude_none=True,
    ).encode("utf-8") + b"\n"
    assert len(expected) >= MIN_TRANSPORT_RESPONSE_BYTES
    assert len(json.dumps(escaped_value).encode("utf-8")) > len(
        escaped_value.encode("utf-8")
    )

    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        transport_response_bytes=len(expected),
    )
    budget = QueryWorkBudget(limits)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            '{"jsonrpc":"2.0","id":"nested-metadata","method":"ping"}'
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert stdout.payloads == [expected]
    assert b'\\"quoted\\"' in expected
    assert b"\\n" in expected
    assert b"\\\\path" in expected
    assert budget.snapshot().transport_response_bytes == len(expected)


def test_transport_response_overflow_writes_reserved_error() -> None:
    import anyio
    import mcp.types as types

    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "result": {"value": "source-value" * 100},
                },
                separators=(",", ":"),
            )
        ),
        metadata=None,
    )
    response_size = len(
        response.message.model_dump_json(
            by_alias=True,
            exclude_none=True,
        ).encode("utf-8")
    ) + 1
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        transport_response_bytes=MIN_TRANSPORT_RESPONSE_BYTES,
    )
    budget = QueryWorkBudget(limits)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            '{"jsonrpc":"2.0","id":7,"method":"ping"}'
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert response_size > limits.transport_response_bytes
    assert len(stdout.payloads) == 1
    assert b"source-value" not in stdout.payloads[0]
    error_message = types.JSONRPCMessage.model_validate_json(stdout.payloads[0])
    assert isinstance(error_message.root, types.JSONRPCError)
    assert error_message.root.id == 7
    assert error_message.root.error.code == -32001
    assert error_message.root.error.message == "response exceeds transport budget"
    assert stdout.flush_count == 1
    assert budget.snapshot().transport_response_bytes == len(stdout.payloads[0])


def test_transport_escaping_expansion_writes_bounded_overflow_error() -> None:
    import anyio
    import mcp.types as types

    source_value = "source\n" * 40
    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "result": {"metadata": {"escaped": source_value}},
                },
                separators=(",", ":"),
            )
        ),
        metadata=None,
    )
    serialized = response.message.model_dump_json(
        by_alias=True,
        exclude_none=True,
    ).encode("utf-8") + b"\n"
    escaping_growth = len(json.dumps(source_value).encode("utf-8")) - len(
        source_value.encode("utf-8")
    )
    assert len(serialized) > MIN_TRANSPORT_RESPONSE_BYTES
    assert len(serialized) - escaping_growth <= MIN_TRANSPORT_RESPONSE_BYTES

    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        transport_response_bytes=MIN_TRANSPORT_RESPONSE_BYTES,
    )
    budget = QueryWorkBudget(limits)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            '{"jsonrpc":"2.0","id":11,"method":"ping"}'
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert b"source" not in stdout.payloads[0]
    error_message = types.JSONRPCMessage.model_validate_json(stdout.payloads[0])
    assert isinstance(error_message.root, types.JSONRPCError)
    assert error_message.root.id == 11
    assert error_message.root.error.code == -32001
    assert len(stdout.payloads[0]) <= MIN_TRANSPORT_RESPONSE_BYTES
    assert budget.snapshot().transport_response_bytes == len(stdout.payloads[0])


@pytest.mark.parametrize(
    "request_id",
    [
        "a" * 254,
        "é" * 127,
        "\\" * 127,
    ],
    ids=("ascii", "unicode", "escaped"),
)
def test_reserved_transport_error_fits_maximum_request_id(request_id: str) -> None:
    import anyio
    import mcp.types as types

    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        transport_response_bytes=MIN_TRANSPORT_RESPONSE_BYTES,
    )
    budget = QueryWorkBudget(limits)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": "ping"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"value": "x" * MIN_TRANSPORT_RESPONSE_BYTES},
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=None,
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert len(stdout.payloads[0]) == MIN_TRANSPORT_RESPONSE_BYTES
    error_message = types.JSONRPCMessage.model_validate_json(stdout.payloads[0])
    assert isinstance(error_message.root, types.JSONRPCError)
    assert error_message.root.id == request_id


@pytest.mark.parametrize(
    "request_id",
    [
        "a" * 254,
        "é" * 127,
        "\\" * 127,
    ],
    ids=("ascii", "unicode", "escaped"),
)
@pytest.mark.parametrize("response_kind", ["result", "error"])
def test_jsonrpc_request_id_at_serialized_cap_is_bounded_in_responses(
    request_id: str,
    response_kind: str,
) -> None:
    import anyio
    import mcp.types as types

    serialized_id = json.dumps(
        request_id,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    assert len(serialized_id) == transport._MAX_JSONRPC_REQUEST_ID_BYTES

    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": "ping"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    response_body: dict[str, Any]
    if response_kind == "result":
        response_body = {"result": {}}
    else:
        response_body = {
            "error": {"code": -32603, "message": "bounded error"}
        }
    response = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, **response_body},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=None,
    )
    registry = transport._RequestBudgetRegistry()
    registry.register_incoming_request(request)
    stdout = RecordingStdout()

    anyio.run(
        transport._write_bounded_session_message,
        stdout,
        response,
        registry,
    )

    assert len(stdout.payloads) == 1
    assert budget.snapshot().transport_response_bytes == len(stdout.payloads[0])


@pytest.mark.parametrize(
    "request_id",
    [
        "a" * 255,
        "é" * 128,
        "\\" * 128,
    ],
    ids=("ascii", "unicode", "escaped"),
)
def test_jsonrpc_request_id_over_serialized_cap_is_rejected(
    request_id: str,
) -> None:
    import mcp.types as types

    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS)
    request = SimpleNamespace(
        message=types.JSONRPCMessage.model_validate_json(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": "ping"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
        metadata=SimpleNamespace(request_context=budget),
    )
    registry = transport._RequestBudgetRegistry()

    with pytest.raises(ValueError, match="256-byte serialized limit") as error:
        registry.register_incoming_request(request)

    assert request_id not in str(error.value)
    assert budget.snapshot().transport_response_bytes == 0


def test_raw_transport_reader_discards_oversized_frame() -> None:
    async def collect_payloads() -> list[Any]:
        import anyio

        stdin = anyio.wrap_file(io.BytesIO(b"123456789\n{}\n"))
        return [
            payload
            async for payload in transport._bounded_raw_payloads(stdin, 5)
        ]

    import anyio

    payloads = anyio.run(collect_payloads)

    assert len(payloads) == 2
    assert payloads[0].attempted_bytes == 6
    assert payloads[1] == b"{}\n"


def test_raw_transport_exhaustion_closes_input_without_later_frames() -> None:
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, raw_transport_payload_bytes=5)

    def create_budget(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    async def receive_failure() -> Exception:
        import anyio

        stdin = anyio.wrap_file(io.BytesIO(b"123456789\n{}\n"))
        stdout = anyio.wrap_file(io.BytesIO())
        async with transport.bounded_stdio_server(
            max_payload_bytes=limits.raw_transport_payload_bytes,
            request_context_factory=create_budget,
            stdin=stdin,
            stdout=stdout,
        ) as (read_stream, write_stream):
            async with read_stream, write_stream:
                failure = await read_stream.receive()
                with pytest.raises(anyio.EndOfStream):
                    await read_stream.receive()
        assert isinstance(failure, Exception)
        return failure

    import anyio

    failure = anyio.run(receive_failure)

    assert isinstance(failure, QueryWorkBudgetExceeded)
    assert failure.dimension.value == "raw transport payload bytes"


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


def test_transport_rejects_canonical_arguments_before_tool_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    audit_key_bytes = b"k" * 32
    log_path = tmp_path / "canonical-budget-audit.jsonl"

    def list_schemas(catalog: str) -> list[str]:
        calls.append(catalog)
        return []

    argument_size = canonical_argument_size(list_schemas, "analytics")
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        canonical_argument_bytes=argument_size - 1,
    )
    monkeypatch.setenv(AUDIT_LOG_ENV, str(log_path))
    monkeypatch.setenv(
        AUDIT_HMAC_KEY_ENV,
        base64.b64encode(audit_key_bytes).decode("ascii"),
    )
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_ACTOR", raising=False)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)

    mcp = transport.create_trino_mcp(
        (with_query_work_budget(list_schemas, limits),)
    )

    assert isinstance(mcp, FakeMCP)
    with pytest.raises(QueryWorkBudgetExceeded, match="canonical argument bytes"):
        mcp.tools[0](catalog="analytics")
    assert calls == []
    records = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [(record["status"], record.get("error_type")) for record in records] == [
        ("started", None),
        ("failed", "QueryWorkBudgetExceeded"),
    ]
    assert verify_audit_log(log_path, audit_key_bytes).record_count == 2
    assert "analytics" not in log_path.read_text(encoding="utf-8")


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
    tools = tuple(server.trino_mcp_services())

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
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_services()))

    assert isinstance(mcp, FakeMCP)
    outputs = {
        tool.__name__: tool(**required_tool_arguments(tool))
        for tool in mcp.tools
    }

    assert tuple(outputs) == DEFAULT_TRINO_TOOL_NAMES
    assert profiler.calls == list(DEFAULT_TRINO_TOOL_NAMES)
    serialized = json.dumps(outputs, sort_keys=True)
    assert_source_literals_absent(json.loads(serialized))
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
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_services()))

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
    assert_source_literals_absent(json.loads(serialized))
    assert "transport-source-literal-condition" not in serialized
    assert "transport-source-literal-allowed" not in serialized


def test_transport_database_errors_are_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(
        failure_message="database request failed",
        failure_type=ConnectionError,
    )
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_LOG", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.setattr(server, "_trino_profiler", lambda: profiler)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_services()))

    assert isinstance(mcp, FakeMCP)
    errors: dict[str, dict[str, str]] = {}
    for tool in mcp.tools:
        with pytest.raises(ConnectionError) as error_info:
            tool(**required_tool_arguments(tool))
        errors[tool.__name__] = {
            "type": type(error_info.value).__name__,
            "message": str(error_info.value),
        }

    assert tuple(errors) == DEFAULT_TRINO_TOOL_NAMES
    assert profiler.calls == list(DEFAULT_TRINO_TOOL_NAMES)
    serialized = json.dumps(errors, sort_keys=True)
    assert_source_literals_absent(json.loads(serialized))
    assert "transport-source-literal-condition" not in serialized
    assert "transport-source-literal-allowed" not in serialized


def test_transport_nested_responses_round_trip_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(nested=True)
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_LOG", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.setattr(server, "_trino_profiler", lambda: profiler)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_services()))

    assert isinstance(mcp, FakeMCP)
    outputs = {
        tool.__name__: tool(**required_tool_arguments(tool))
        for tool in mcp.tools
    }
    serialized = json.dumps(outputs, sort_keys=True)

    assert json.loads(serialized) == outputs
    assert_source_literals_absent(json.loads(serialized))
    assert outputs["describe_table"][0]["metadata"] == {"nullable": True}
    for name, output in outputs.items():
        if name.startswith("profile_"):
            assert output["summary"]["columns"][0]["metrics"] == {
                "null_ratio": 0.0
            }
    assert "transport-source-literal-condition" not in serialized
    assert "transport-source-literal-allowed" not in serialized


def test_default_tool_audit_records_are_metadata_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    audit_key_bytes = b"k" * 32
    log_path = tmp_path / "trino-audit.jsonl"
    monkeypatch.setenv(AUDIT_LOG_ENV, str(log_path))
    monkeypatch.setenv(
        AUDIT_HMAC_KEY_ENV,
        base64.b64encode(audit_key_bytes).decode("ascii"),
    )
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_ACTOR", raising=False)
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(transport, "FastMCP", FakeMCP)

    success_profiler = RecordingProfiler()
    monkeypatch.setattr(server, "_trino_profiler", lambda: success_profiler)
    mcp = transport.create_trino_mcp(tuple(server.trino_mcp_services()))
    assert isinstance(mcp, FakeMCP)
    for tool in mcp.tools:
        tool(**required_tool_arguments(tool))

    failure_profiler = RecordingProfiler(
        failure_message="database request failed",
        failure_type=ConnectionError,
    )
    monkeypatch.setattr(server, "_trino_profiler", lambda: failure_profiler)
    for tool in mcp.tools:
        with pytest.raises(ConnectionError):
            tool(**required_tool_arguments(tool))

    records = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert_source_literals_absent(records)
    expected_events = [
        (name, status)
        for name in DEFAULT_TRINO_TOOL_NAMES
        for status in ("started", "succeeded")
    ] + [
        (name, status)
        for name in DEFAULT_TRINO_TOOL_NAMES
        for status in ("started", "failed")
    ]
    assert [(record["operation"], record["status"]) for record in records] == (
        expected_events
    )
    assert verify_audit_log(log_path, audit_key_bytes).record_count == len(records)
    base_record_keys = {
        "event_id",
        "invocation_id",
        "mac",
        "operation",
        "previous_mac",
        "schema_version",
        "sequence",
        "service",
        "status",
        "timestamp",
    }
    for record in records:
        expected_keys = base_record_keys | (
            {"error_type"} if record["status"] == "failed" else set()
        )
        assert set(record) == expected_keys
        assert record["service"] == "trino-mcp"

    audit_text = log_path.read_text(encoding="utf-8")
    for source_literal in (
        "analytics",
        "safe_schema",
        "synthetic_orders",
        "transport-source-literal-condition",
        "transport-source-literal-allowed",
    ):
        assert source_literal not in audit_text


def test_trino_transport_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport, "FastMCP", None)

    assert transport.create_trino_mcp(()) is None
