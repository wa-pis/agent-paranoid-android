"""Transport registration for allowlisted Trino MCP services."""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import Any

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[misc, assignment]

from test_data_agent.audit import audited_mcp_tool
from test_data_agent.trino_work_budget import (
    MIN_TRANSPORT_RESPONSE_BYTES,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
)


RawRequestContextFactory = Callable[[int], QueryWorkBudget]
_INVALID_TOOL_ARGUMENTS_MESSAGE = "Tool arguments failed validation"
_MAX_JSONRPC_REQUEST_ID_BYTES = 256
DEFAULT_MAX_ACTIVE_MCP_REQUESTS = 32
_TRANSPORT_OVERFLOW_ERROR_PREFIX = b'{"jsonrpc":"2.0","id":'
_TRANSPORT_OVERFLOW_ERROR_SUFFIX = (
    b',"error":{"code":-32001,'
    b'"message":"response exceeds transport budget"}}\n'
)
_TRANSPORT_CAPACITY_ERROR_SUFFIX = (
    b',"error":{"code":-32002,'
    b'"message":"server request capacity exhausted"}}\n'
)
_RESERVED_TRANSPORT_ERROR_BYTES = (
    len(_TRANSPORT_OVERFLOW_ERROR_PREFIX)
    + _MAX_JSONRPC_REQUEST_ID_BYTES
    + len(_TRANSPORT_OVERFLOW_ERROR_SUFFIX)
)
if _RESERVED_TRANSPORT_ERROR_BYTES != MIN_TRANSPORT_RESPONSE_BYTES:
    raise RuntimeError("transport overflow error reservation is inconsistent")
if (
    len(_TRANSPORT_OVERFLOW_ERROR_PREFIX)
    + _MAX_JSONRPC_REQUEST_ID_BYTES
    + len(_TRANSPORT_CAPACITY_ERROR_SUFFIX)
    > MIN_TRANSPORT_RESPONSE_BYTES
):
    raise RuntimeError("transport capacity error exceeds reserved response bytes")


@dataclass(frozen=True, slots=True)
class _OversizedRawPayload:
    attempted_bytes: int


class DuplicateActiveRequestIdError(ValueError):
    """Raised when a second request reuses an active JSON-RPC ID."""


class ActiveRequestCapacityError(RuntimeError):
    """Raised when the process-wide MCP request cap is exhausted."""


def _create_redacted_fast_mcp(name: str, fast_mcp_type: type[Any]) -> Any:
    """Create FastMCP with source-free argument validation failures."""

    class RedactedFastMCP(fast_mcp_type):  # type: ignore[misc]
        async def call_tool(
            self,
            tool_name: str,
            arguments: dict[str, Any],
        ) -> Any:
            from mcp.server.fastmcp.exceptions import ToolError
            from pydantic import ValidationError

            try:
                return await super().call_tool(tool_name, arguments)
            except ToolError as exc:
                if isinstance(exc.__cause__, ValidationError):
                    raise ToolError(_INVALID_TOOL_ARGUMENTS_MESSAGE) from None
                raise

    return RedactedFastMCP(name)


class _RequestBudgetRegistry:
    """Associate response messages with the budget of their input request."""

    __slots__ = ("_budgets", "_max_active_requests")

    def __init__(
        self,
        max_active_requests: int = DEFAULT_MAX_ACTIVE_MCP_REQUESTS,
    ) -> None:
        if max_active_requests <= 0:
            raise ValueError("max_active_requests must be positive")
        self._budgets: dict[bytes, QueryWorkBudget] = {}
        self._max_active_requests = max_active_requests

    def register_incoming_request(self, session_message: Any) -> None:
        import mcp.types as types

        root = session_message.message.root
        if not isinstance(root, types.JSONRPCRequest):
            if hasattr(root, "id"):
                raise ValueError("JSON-RPC request ID must be a string or integer")
            return
        _validate_jsonrpc_request_id(root.id)
        request_key = _jsonrpc_request_id_key(root.id)
        if request_key in self._budgets:
            raise DuplicateActiveRequestIdError(
                "JSON-RPC request ID is already active"
            )
        if len(self._budgets) >= self._max_active_requests:
            raise ActiveRequestCapacityError("MCP request capacity exhausted")
        budget = getattr(session_message.metadata, "request_context", None)
        if not isinstance(budget, QueryWorkBudget):
            raise TypeError("MCP request context must be a QueryWorkBudget")
        self._budgets[request_key] = budget

    def resolve_outgoing(self, session_message: Any) -> QueryWorkBudget | None:
        import mcp.types as types

        root = session_message.message.root
        if isinstance(root, (types.JSONRPCResponse, types.JSONRPCError)):
            try:
                return self._budgets[_jsonrpc_request_id_key(root.id)]
            except KeyError as exc:
                raise RuntimeError(
                    "MCP response has no registered request budget"
                ) from exc

        related_request_id = getattr(
            session_message.metadata,
            "related_request_id",
            None,
        )
        if related_request_id is None:
            return None
        return self._budgets.get(_jsonrpc_request_id_key(related_request_id))

    def complete_outgoing(self, session_message: Any) -> None:
        import mcp.types as types

        root = session_message.message.root
        if isinstance(root, (types.JSONRPCResponse, types.JSONRPCError)):
            self._budgets.pop(_jsonrpc_request_id_key(root.id), None)

    def clear(self) -> None:
        self._budgets.clear()


def _validate_jsonrpc_request_id(request_id: Any) -> None:
    if isinstance(request_id, bool) or not isinstance(request_id, (str, int)):
        raise ValueError("JSON-RPC request ID must be a string or integer")
    serialized = _serialize_jsonrpc_request_id(request_id)
    if len(serialized) > _MAX_JSONRPC_REQUEST_ID_BYTES:
        raise ValueError(
            "JSON-RPC request ID exceeds the 256-byte serialized limit"
        )


def _jsonrpc_request_id_key(request_id: Any) -> bytes:
    _validate_jsonrpc_request_id(request_id)
    return _serialize_jsonrpc_request_id(request_id)


def _serialize_jsonrpc_request_id(request_id: Any) -> bytes:
    return json.dumps(
        request_id,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _transport_overflow_error_payload(request_id: Any) -> bytes:
    serialized_id = _serialize_jsonrpc_request_id(request_id)
    if len(serialized_id) > _MAX_JSONRPC_REQUEST_ID_BYTES:
        raise ValueError("cannot reflect an oversized JSON-RPC request ID")
    return (
        _TRANSPORT_OVERFLOW_ERROR_PREFIX
        + serialized_id
        + _TRANSPORT_OVERFLOW_ERROR_SUFFIX
    )


def _transport_capacity_error_payload(request_id: Any) -> bytes:
    serialized_id = _serialize_jsonrpc_request_id(request_id)
    if len(serialized_id) > _MAX_JSONRPC_REQUEST_ID_BYTES:
        raise ValueError("cannot reflect an oversized JSON-RPC request ID")
    return (
        _TRANSPORT_OVERFLOW_ERROR_PREFIX
        + serialized_id
        + _TRANSPORT_CAPACITY_ERROR_SUFFIX
    )


async def _write_bounded_session_message(
    stdout: Any,
    session_message: Any,
    budget_registry: _RequestBudgetRegistry,
) -> None:
    """Serialize, charge, and write one production-framed MCP message."""
    try:
        payload = session_message.message.model_dump_json(
            by_alias=True,
            exclude_none=True,
        ).encode("utf-8") + b"\n"
        budget = budget_registry.resolve_outgoing(session_message)
        if budget is not None:
            try:
                budget.consume_transport_response_bytes(len(payload))
            except QueryWorkBudgetExceeded:
                import mcp.types as types

                root = session_message.message.root
                if not isinstance(root, (types.JSONRPCResponse, types.JSONRPCError)):
                    raise
                payload = _transport_overflow_error_payload(root.id)
                budget.consume_terminal_error_bytes(len(payload))
        await stdout.write(payload)
        await stdout.flush()
    finally:
        budget_registry.complete_outgoing(session_message)


async def _bounded_raw_payloads(
    stdin: Any,
    max_payload_bytes: int,
) -> AsyncIterator[bytes | _OversizedRawPayload]:
    """Read newline-framed payloads without retaining an oversized frame."""
    if max_payload_bytes <= 0:
        raise ValueError("max_payload_bytes must be positive")

    pending = bytearray()
    discarding = False
    chunk_size = min(64 * 1024, max_payload_bytes + 1)
    while chunk := await stdin.read(chunk_size):
        if not isinstance(chunk, bytes):
            raise TypeError("bounded MCP stdin must be a binary stream")
        offset = 0
        while offset < len(chunk):
            newline = chunk.find(b"\n", offset)
            end = newline + 1 if newline >= 0 else len(chunk)
            piece = chunk[offset:end]
            offset = end

            if discarding:
                if newline >= 0:
                    discarding = False
                continue

            attempted = len(pending) + len(piece)
            if attempted > max_payload_bytes:
                pending.clear()
                discarding = newline < 0
                yield _OversizedRawPayload(attempted)
                continue

            pending.extend(piece)
            if newline >= 0:
                yield bytes(pending)
                pending.clear()

    if pending and not discarding:
        yield bytes(pending)


def _bounded_session_message(
    raw_payload: bytes,
    request_context_factory: RawRequestContextFactory,
) -> Any:
    """Attach a request budget only after charging bytes and before parsing."""
    request_context = request_context_factory(len(raw_payload))
    _consume_json_structure(raw_payload, request_context)

    raw_message = json.loads(raw_payload)
    if (
        isinstance(raw_message, dict)
        and "method" in raw_message
        and "id" in raw_message
    ):
        _validate_jsonrpc_request_id(raw_message["id"])

    import mcp.types as types
    from mcp.shared.message import ServerMessageMetadata, SessionMessage

    message = types.JSONRPCMessage.model_validate_json(raw_payload)
    return SessionMessage(
        message,
        metadata=ServerMessageMetadata(request_context=request_context),
    )


def _consume_json_structure(
    raw_payload: bytes,
    budget: QueryWorkBudget,
) -> None:
    """Bound JSON depth, nodes, and scalar bytes before materialization."""
    depth = 0
    in_string = False
    escaped = False
    scalar_bytes = 0
    primitive_bytes = 0
    scalar_limit = budget.limits.canonical_argument_bytes

    for byte in raw_payload:
        if in_string:
            if escaped:
                escaped = False
                scalar_bytes += 1
            elif byte == ord("\\"):
                escaped = True
                scalar_bytes += 1
            elif byte == ord('"'):
                in_string = False
                budget.consume_ast_nodes(1)
                scalar_bytes = 0
            else:
                scalar_bytes += 1
            if scalar_bytes > scalar_limit:
                raise ValueError("JSON scalar exceeds structural limit")
            continue

        if byte == ord('"'):
            if primitive_bytes:
                budget.consume_ast_nodes(1)
                primitive_bytes = 0
            in_string = True
        elif byte in (ord("{"), ord("[")):
            if primitive_bytes:
                budget.consume_ast_nodes(1)
                primitive_bytes = 0
            depth += 1
            budget.consume_ast_nodes(1)
            budget.observe_ast_depth(depth)
        elif byte in (ord("}"), ord("]")):
            if primitive_bytes:
                budget.consume_ast_nodes(1)
                primitive_bytes = 0
            depth = max(0, depth - 1)
        elif byte in b" \t\r\n,:":
            if primitive_bytes:
                budget.consume_ast_nodes(1)
                primitive_bytes = 0
        else:
            primitive_bytes += 1
            if primitive_bytes > scalar_limit:
                raise ValueError("JSON scalar exceeds structural limit")

    if primitive_bytes:
        budget.consume_ast_nodes(1)


@asynccontextmanager
async def bounded_stdio_server(
    *,
    max_payload_bytes: int,
    request_context_factory: RawRequestContextFactory,
    max_active_requests: int = DEFAULT_MAX_ACTIVE_MCP_REQUESTS,
    stdin: Any | None = None,
    stdout: Any | None = None,
) -> AsyncIterator[tuple[Any, Any]]:
    """Provide MCP stdio streams with a pre-parse raw payload limit."""
    import anyio
    import anyio.lowlevel

    if stdin is None:
        binary_stdin: Any = sys.stdin.buffer
        stdin = anyio.wrap_file(binary_stdin.raw)
    if stdout is None:
        stdout = anyio.wrap_file(sys.stdout.buffer)

    read_stream_writer: Any
    read_stream: Any
    write_stream: Any
    write_stream_reader: Any
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)
    budget_registry = _RequestBudgetRegistry(max_active_requests)
    output_lock = anyio.Lock()

    async def stdin_reader() -> None:
        try:
            async with read_stream_writer:
                async for payload in _bounded_raw_payloads(
                    stdin,
                    max_payload_bytes,
                ):
                    if isinstance(payload, _OversizedRawPayload):
                        try:
                            request_context_factory(payload.attempted_bytes)
                        except Exception as exc:
                            await read_stream_writer.send(exc)
                        else:  # pragma: no cover - factory must enforce the limit.
                            await read_stream_writer.send(
                                ValueError("raw MCP payload exceeds configured limit")
                            )
                        return
                    try:
                        message = _bounded_session_message(
                            payload,
                            request_context_factory,
                        )
                        budget_registry.register_incoming_request(message)
                    except ActiveRequestCapacityError:
                        root = message.message.root
                        payload = _transport_capacity_error_payload(root.id)
                        budget = message.metadata.request_context
                        budget.consume_terminal_error_bytes(len(payload))
                        async with output_lock:
                            await stdout.write(payload)
                            await stdout.flush()
                        continue
                    except Exception as exc:
                        await read_stream_writer.send(exc)
                        continue
                    await read_stream_writer.send(message)
        except anyio.ClosedResourceError:  # pragma: no cover
            await anyio.lowlevel.checkpoint()

    async def stdout_writer() -> None:
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    async with output_lock:
                        await _write_bounded_session_message(
                            stdout,
                            session_message,
                            budget_registry,
                        )
        except anyio.ClosedResourceError:  # pragma: no cover
            await anyio.lowlevel.checkpoint()

    try:
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(stdin_reader)
            task_group.start_soon(stdout_writer)
            yield read_stream, write_stream
    finally:
        budget_registry.clear()


async def _run_bounded_stdio(
    mcp: Any,
    *,
    max_payload_bytes: int,
    request_context_factory: RawRequestContextFactory,
) -> None:
    async with bounded_stdio_server(
        max_payload_bytes=max_payload_bytes,
        request_context_factory=request_context_factory,
    ) as (read_stream, write_stream):
        low_level_server = mcp._mcp_server
        await low_level_server.run(
            read_stream,
            write_stream,
            low_level_server.create_initialization_options(),
        )


def run_bounded_mcp(
    mcp: Any,
    *,
    max_payload_bytes: int,
    request_context_factory: RawRequestContextFactory,
) -> None:
    """Run a FastMCP server with the bounded binary stdio transport."""
    import anyio

    anyio.run(
        partial(
            _run_bounded_stdio,
            mcp,
            max_payload_bytes=max_payload_bytes,
            request_context_factory=request_context_factory,
        )
    )


run_bounded_trino_mcp = run_bounded_mcp


def create_trino_mcp(
    tools: Sequence[Callable[..., Any]],
) -> Any | None:
    """Register audited services without owning their SQL safety policy."""

    if FastMCP is None:
        return None

    mcp = _create_redacted_fast_mcp("test-data-agent-trino", FastMCP)
    for tool in tools:
        mcp.tool()(audited_mcp_tool("trino-mcp", tool))
    return mcp
