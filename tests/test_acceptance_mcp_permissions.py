"""Actual stdio permission/discovery checks; Trino acquisition is a stand-in."""

import asyncio
import base64
from datetime import timedelta
from importlib.metadata import version
from importlib.util import find_spec
import json
import os
from pathlib import Path
import sys
import sysconfig

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
                    assert len(expected) == 16
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


def _parquet_client_parameters(workspace, **settings):
    command = Path(sysconfig.get_path("scripts")) / "test-data-agent-mcp-generator"
    assert command.is_file(), "install the candidate package before the stdio test"
    return StdioServerParameters(
        command=str(command), cwd=str(workspace), env={**_environment(workspace), **settings},
    )


def test_generator_stdio_parquet_profile_and_review_first_plan(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.core.dataset import DatasetProfile

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    value = "fictional.person@example.invalid"
    embedded_metadata = "fictional-private-file-metadata"
    row_count = 10_001
    table = pa.table({
        "sequence": range(row_count),
        "pattern": [1, None] + [2] * (row_count - 2),
        "note": [value] * row_count,
    }).replace_schema_metadata({b"private_note": embedded_metadata.encode()})
    pq.write_table(table, workspace / "source.parquet")
    pq.write_table(pa.table({"blob": [b"fictional-private-bytes", None]}),
                   workspace / "unknown.parquet", write_statistics=False)
    pq.write_table(pa.table({"sequence": range(row_count + 1)}), workspace / "too-many.parquet")
    pq.write_table(pa.table({value: [1]}), workspace / "sensitive-column.parquet")

    outside = tmp_path / "fictional-private-outside.parquet"
    outside.write_bytes((workspace / "source.parquet").read_bytes())
    (workspace / "escape.parquet").symlink_to(outside)
    (workspace / "dangling.json").symlink_to(workspace / "not-created.json")
    (workspace / "fictional-private-malformed.parquet").write_text("fictional-private-bad-payload")
    (workspace / "wrong-suffix.csv").write_text("quantity\n1\n")
    (workspace / "already.json").write_text("existing artifact")
    os.mkfifo(workspace / "fifo.parquet")
    parameters = _parquet_client_parameters(workspace, TEST_DATA_AGENT_MAX_INPUT_ROWS=str(row_count))
    responses = []

    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()
                    tools = {tool.name for tool in (await client.list_tools()).tools}
                    assert {"profile_csv", "profile_parquet", "plan_dataset"} <= tools

                    async def call(name, arguments, *, error=False):
                        result = await client.call_tool(name, arguments)
                        assert result.model_dump(by_alias=True)["isError"] is error
                        responses.append(result.model_dump_json())
                        if not error:
                            return json.loads(next(item.text for item in result.content if item.type == "text"))

                    summary = await call("profile_parquet", {
                        "input_path": "source.parquet", "output_path": "reports/profile.json",
                        "table_name": "records",
                    })
                    assert summary == {
                        "operation": "profile_parquet", "source_type": "parquet",
                        "profile_path": "reports/profile.json", "entity_count": 1,
                        "entities": [{"name": "records", "row_count": row_count,
                                      "field_count": 3, "sensitive_field_count": 1}],
                    }
                    await call("profile_parquet", {"input_path": "unknown.parquet", "output_path": "unknown.json"})
                    plan = await call("plan_dataset", {
                        "source_path": summary["profile_path"], "source_type": "profile",
                        "workspace_path": "plan", "count": 4, "seed": 7,
                    })
                    state = await call("inspect_dataset_plan", {"workspace_path": "plan"})
                    assert plan["approval_required"] and state["approval_required"]
                    assert len(state["review"]["current_spec_sha256"]) == 64
                    assert (workspace / plan["spec_path"]).is_file()
                    assert not (workspace / "plan/generated").exists()
                    for source, output in [
                        ("../fictional-private-outside.parquet", "refused.json"),
                        ("escape.parquet", "refused.json"),
                        ("fifo.parquet", "refused.json"),
                        ("fictional-private-malformed.parquet", "refused.json"),
                        ("sensitive-column.parquet", "refused.json"),
                        ("wrong-suffix.csv", "refused.json"),
                        ("too-many.parquet", "refused.json"),
                        ("source.parquet", "../refused.json"),
                        ("source.parquet", "already.json"),
                        ("source.parquet", "dangling.json"),
                        ("source.parquet", "source.parquet"),
                    ]:
                        await call("profile_parquet", {"input_path": source, "output_path": output}, error=True)
            errors.seek(0)
            responses.append(errors.read())

    asyncio.run(asyncio.wait_for(run(), timeout=40))
    saved = (workspace / "reports/profile.json").read_text()
    unknown = (workspace / "unknown.json").read_text()
    entity = DatasetProfile.model_validate_json(saved).entity("records")
    assert entity.primary_key_candidates == []
    assert entity.field("sequence").unique_ratio_kind == "lower_bound"
    assert entity.field("sequence").unique_ratio == 10_000 / row_count
    assert entity.field("pattern").unique_ratio_kind == "exact"
    assert entity.field("note").sensitive
    unknown_field = DatasetProfile.model_validate_json(unknown).entity("unknown").field("blob")
    assert unknown_field.unique_ratio is None and unknown_field.null_ratio is None
    assert unknown_field.unique_ratio_kind == "unspecified"
    disclosed = "\n".join([saved, unknown, (workspace / "plan/dataset_spec.yaml").read_text(), *responses])
    assert value not in disclosed
    assert "fictional-private-" not in disclosed
    assert str(workspace) not in disclosed
    assert (workspace / "already.json").read_text() == "existing artifact"
    assert (workspace / "dangling.json").is_symlink()
    assert not (workspace / "not-created.json").exists()
    assert not (workspace / "refused.json").exists()
    assert not (tmp_path / "refused.json").exists()
    assert not list(workspace.rglob("*.tmp"))


@pytest.mark.skipif(find_spec("pyarrow") is not None, reason="requires an MCP-only installation")
def test_generator_stdio_without_parquet_extra(tmp_path):
    (tmp_path / "fixture.parquet").write_bytes(b"unused without a decoder")
    (tmp_path / "fixture.csv").write_text("quantity\n1\n2\n")
    parameters = _parquet_client_parameters(tmp_path)

    async def run():
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                await client.initialize()
                assert "profile_parquet" in {tool.name for tool in (await client.list_tools()).tools}
                result = await client.call_tool("profile_parquet", {
                    "input_path": "fixture.parquet", "output_path": "profile.json",
                })
                assert result.model_dump(by_alias=True)["isError"]
                assert "Install agent-paranoid-android[mcp,parquet]" in result.model_dump_json()
                assert not (tmp_path / "profile.json").exists()
                result = await client.call_tool("profile_csv", {
                    "input_path": "fixture.csv", "output_path": "profile.json",
                })
                assert not result.model_dump(by_alias=True)["isError"]
                assert (tmp_path / "profile.json").is_file()

    asyncio.run(asyncio.wait_for(run(), timeout=40))


@pytest.mark.parametrize("rule_kind", ["row", "aggregate"])
def test_generator_stdio_formula_privacy_refuses_every_publication_format(tmp_path, rule_kind):
    (tmp_path / "spec.json").write_text(json.dumps({
        "entities": [{"name": "records", "row_count": 1, "fields": [{
            "name": "phone", "data_type": "integer", "sensitive": True,
            "distribution": {"kind": "numeric", "min_value": 1,
                             "max_value": 9, "scale_factor": 2},
        }]}],
        "business_rules": {"row_rules": [{"type": "formula", "table": "records",
            "field": "phone", "expression": "123456789"}]} if rule_kind == "row" else {
                "cross_table_rules": [{"type": "aggregate_formula", "table": "records",
                    "field": "phone", "expression": "123456789"}]},
        "validation_settings": {"validate_privacy": False},
    }))
    parameters = StdioServerParameters(command=sys.executable,
        args=["-m", "test_data_agent.mcp_generator_server"],
        env=_environment(tmp_path), cwd=str(Path(__file__).resolve().parents[1]))

    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()
                    for tool in ("generate_dataset", "export_dataset"):
                        for output_format in ("csv", "json", "parquet", "sql"):
                            output = f"{tool}-{output_format}"
                            result = await client.call_tool(tool, {"spec_path": "spec.json",
                                "output_folder": output, "output_format": output_format})
                            assert result.model_dump(by_alias=True)["isError"]
                            assert "123456789" not in result.model_dump_json()
                            assert not (tmp_path / output).exists()
            errors.seek(0)
            assert "123456789" not in errors.read()

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
