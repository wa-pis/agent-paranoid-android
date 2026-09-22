"""Real stdio SDK coverage; no database or external network is used."""
import json
import selectors
import subprocess
import sys
from pathlib import Path


def test_sdk_stdio_preserves_request_budget_and_redacts_errors(tmp_path: Path) -> None:
    program = '''
from test_data_agent.mcp_generator_transport import create_generator_mcp
from test_data_agent.mcp_generator_server import _new_transport_work_budget
from test_data_agent.mcp_trino_transport import run_bounded_mcp
from test_data_agent.trino_work_budget import QueryWorkBudget, DEFAULT_QUERY_WORK_LIMITS
def probe(limit: int) -> str:
    budget = server.get_context().request_context.request
    assert isinstance(budget, QueryWorkBudget)
    if limit < 0:
        raise RuntimeError("synthetic-private-tool-marker")
    return "shared-budget"
server = create_generator_mcp((probe,))
run_bounded_mcp(server, max_payload_bytes=DEFAULT_QUERY_WORK_LIMITS.raw_transport_payload_bytes,
    request_context_factory=_new_transport_work_budget)
'''
    with (tmp_path / "stderr.txt").open("w+") as errors:
        process = subprocess.Popen(
            [sys.executable, "-c", program], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=errors, text=True,
        )
        assert process.stdin is not None and process.stdout is not None

        def send(message: dict) -> None:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        def receive() -> dict:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=15), "MCP response deadline exceeded"
            return json.loads(process.stdout.readline())

        try:
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-03-26", "capabilities": {},
                "clientInfo": {"name": "synthetic-test", "version": "1"}}})
            assert "result" in receive()
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            for request_id, value in [(2, 1), (3, "synthetic-invalid-argument")]:
                send({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                      "params": {"name": "probe", "arguments": {"limit": value}}})
                response = receive()
                assert response["id"] == request_id
                payload = json.dumps(response)
                assert ("shared-budget" if request_id == 2 else "Tool arguments failed validation") in payload
                assert "synthetic-invalid-argument" not in payload
            # Only SDK 2 changes unexpected-error logging; test its full wire path.
            from importlib.metadata import version
            if int(version("mcp").split(".")[0]) >= 2:
                send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                      "params": {"name": "probe", "arguments": {"limit": -1}}})
                assert "Tool execution failed" in json.dumps(receive())
            process.stdin.close()
            assert process.wait(timeout=10) == 0
            errors.seek(0)
            logs = errors.read()
            assert "synthetic-invalid-argument" not in logs
            assert "synthetic-private-tool-marker" not in logs
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
