"""Invoke the SDK's actual error handler on either supported major."""
from types import SimpleNamespace
from typing import Any


async def call_tool_handler(server: Any, request: Any) -> Any:
    if hasattr(server, "_mcp_server"):
        import mcp.types as types
        return await server._mcp_server.request_handlers[types.CallToolRequest](request)
    result = await server._handle_call_tool(None, request.params)
    return SimpleNamespace(root=SimpleNamespace(
        isError=result.is_error, model_dump_json=result.model_dump_json,
    ))
