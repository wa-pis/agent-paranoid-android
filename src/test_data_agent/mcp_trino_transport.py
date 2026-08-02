"""Transport registration for allowlisted Trino MCP services."""

from __future__ import annotations

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


RawRequestContextFactory = Callable[[int], object]


@dataclass(frozen=True, slots=True)
class _OversizedRawPayload:
    attempted_bytes: int


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

    import mcp.types as types
    from mcp.shared.message import ServerMessageMetadata, SessionMessage

    message = types.JSONRPCMessage.model_validate_json(raw_payload)
    return SessionMessage(
        message,
        metadata=ServerMessageMetadata(request_context=request_context),
    )


@asynccontextmanager
async def bounded_stdio_server(
    *,
    max_payload_bytes: int,
    request_context_factory: RawRequestContextFactory,
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
                    payload = session_message.message.model_dump_json(
                        by_alias=True,
                        exclude_none=True,
                    ).encode("utf-8")
                    await stdout.write(payload + b"\n")
                    await stdout.flush()
        except anyio.ClosedResourceError:  # pragma: no cover
            await anyio.lowlevel.checkpoint()

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(stdin_reader)
        task_group.start_soon(stdout_writer)
        yield read_stream, write_stream


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


def run_bounded_trino_mcp(
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
