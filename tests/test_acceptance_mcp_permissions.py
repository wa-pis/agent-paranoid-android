"""Actual stdio permission/discovery checks; Trino acquisition is a stand-in."""

import asyncio
import base64
from datetime import timedelta
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest


def _environment(workspace):
    # Test workers never inherit a configured real source or provider.
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("TRINO_", "POSTGRES_", "OPENAI_", "GIGACHAT_", "TEST_DATA_AGENT_"))
                   and key != "PYTHONPATH"}
    environment["TEST_DATA_AGENT_WORKSPACE_ROOT"] = str(workspace)
    return environment


def _timeout():
    return timedelta(seconds=15) if version("mcp").split(".")[0] == "1" else 15


def test_generator_stdio_inventory_and_every_tool_argument_refusal(tmp_path):
    expected = {tool["name"] for tool in json.loads(
        (Path(__file__).parent / "fixtures/contracts/mcp-generator-tools.json").read_text())}
    parameters = StdioServerParameters(command=sys.executable,
        args=["-m", "test_data_agent.mcp_generator_server"],
        env=_environment(tmp_path), cwd=str(Path(__file__).resolve().parents[1]))
    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()
                    tools = (await client.list_tools()).tools
                    assert {tool.name for tool in tools} == expected
                    assert len(expected) == 14
                    assert not any("approve_transformation" in tool.name for tool in tools)
                    for name in sorted(expected):
                        result = await client.call_tool(name, {"fictional-private-extra": True})
                        assert result.model_dump(by_alias=True)["isError"]
                        assert "fictional-private-extra" not in result.model_dump_json()
                    result = await client.call_tool("profile_csv", {
                        "input_path": "../fictional-private-escape.csv", "output_path": "profile.json"})
                    assert result.model_dump(by_alias=True)["isError"]
                    assert "fictional-private-escape" not in result.model_dump_json()
            errors.seek(0)
            assert "fictional-private-extra" not in errors.read()
    asyncio.run(asyncio.wait_for(run(), timeout=40))
    assert [path.name for path in tmp_path.iterdir()] == ["stderr.log"]


def test_generator_stdio_lower_level_synthetic_tools_and_profile_handoff(tmp_path):
    (tmp_path / "customers.csv").write_text(
        "customer_id,label\n1,fictional-source-a\n2,fictional-source-b\n")
    parameters = StdioServerParameters(command=sys.executable,
        args=["-m", "test_data_agent.mcp_generator_server"],
        env=_environment(tmp_path), cwd=str(Path(__file__).resolve().parents[1]))
    responses = []
    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()
                    async def call(name, arguments):
                        result = await client.call_tool(name, arguments)
                        assert not result.model_dump(by_alias=True)["isError"]
                        responses.append(result.model_dump_json())
                        return json.loads(next(item.text for item in result.content if item.type == "text"))
                    await call("profile_csv", {"input_path": "customers.csv", "output_path": "profile.json"})
                    await call("infer_dataset_spec", {"profile_path": "profile.json", "output_path": "spec.yaml", "count": 4})
                    generated = await call("generate_dataset", {"spec_path": "spec.yaml", "output_folder": "generated", "seed": 7})
                    assert generated["row_counts"] == {"customers": 4}
                    checked = await call("validate_dataset", {"spec_path": "generated/dataset_spec.yaml", "rows_folder": "generated", "output_path": "checked.json"})
                    assert checked["validation"]["valid"]
                    exported = await call("export_dataset", {"spec_path": "spec.yaml", "output_folder": "exported", "output_format": "csv", "seed": 7})
                    assert exported["validation"]["valid"]
                    planned = await call("plan_trino_dataset", {"profile_payload": {
                        "source_type": "trino", "table": "items", "row_count": 2,
                        "columns": [{"name": "item_id", "data_type": "bigint", "approx_distinct_count": 2}]},
                        "workspace_path": "agent", "count": 4, "seed": 7})
                    assert planned["approval_required"]
                    assert not (tmp_path / "agent/generated").exists()
            errors.seek(0)
            text = errors.read() + "\n".join(responses)
            assert "fictional-source-a" not in text and "fictional-source-b" not in text
    asyncio.run(asyncio.wait_for(run(), timeout=40))


@pytest.mark.parametrize("row_opt_in", [False, True])
def test_trino_stdio_all_aggregate_tools_with_standin_and_authenticated_audit(tmp_path, row_opt_in):
    """Exercise real transport/dispatch, with an explicitly fictional profiler."""
    from tests.test_mcp_trino_transport import DEFAULT_ARGUMENT_VALUES
    from test_data_agent.audit import verify_audit_log

    program = """
from tests.test_mcp_trino_transport import RecordingProfiler
import test_data_agent.mcp_trino_server as server
server._trino_profiler = lambda: RecordingProfiler()
raise SystemExit(server.main())
"""
    environment = _environment(tmp_path)
    environment.update(TRINO_HOST="fictional.invalid", TRINO_PORT="443", TRINO_USER="fictional_reader",
        TRINO_HTTP_SCHEME="https", TRINO_ALLOWED_CATALOGS="analytics", TRINO_ALLOWED_SCHEMAS="safe_schema",
        TRINO_ENABLE_SAFE_SELECT=str(row_opt_in).lower(),
        TEST_DATA_AGENT_AUDIT_LOG=str(tmp_path / "audit.jsonl"),
        TEST_DATA_AGENT_AUDIT_HMAC_KEY=base64.b64encode(b"k" * 32).decode())
    parameters = StdioServerParameters(command=sys.executable, args=["-c", program],
        env=environment, cwd=str(Path(__file__).resolve().parents[1]))
    responses = []
    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()
                    tools = (await client.list_tools()).tools
                    aggregate = [tool for tool in tools if tool.name != "run_safe_select"]
                    assert len(aggregate) == 13
                    assert ("run_safe_select" in {tool.name for tool in tools}) is row_opt_in
                    for tool in aggregate:
                        schema = tool.model_dump(by_alias=True)["inputSchema"]
                        arguments = {name: DEFAULT_ARGUMENT_VALUES[name] for name in schema.get("required", [])}
                        result = await client.call_tool(tool.name, arguments)
                        assert not result.model_dump(by_alias=True)["isError"]
                        responses.append(result.model_dump_json())
            errors.seek(0)
            text = errors.read() + "\n".join(responses)
            assert "transport-source-literal-condition" not in text
            assert "transport-source-literal-allowed" not in text
    asyncio.run(asyncio.wait_for(run(), timeout=40))
    verification = verify_audit_log(tmp_path / "audit.jsonl", b"k" * 32)
    assert verification.record_count == 26
