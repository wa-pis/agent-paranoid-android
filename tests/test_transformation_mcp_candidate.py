"""Workspace containment for unregistered fictional execution candidate."""

import pytest
import asyncio
import json
import yaml
import os
import sys

from test_data_agent.mcp_generator_server import WorkspacePathError
from test_data_agent.mcp_transformation_candidate import _execute_candidate_transformation


def test_closed_sdk_limit_error_keeps_value_free_recovery(tmp_path, monkeypatch):
    from mcp.server.fastmcp.exceptions import ToolError
    from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp

    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES", "1024")
    (tmp_path / "items.csv").write_text("label\nfictional-source-marker\n")
    (tmp_path / "policy.yaml").write_text("fictional-policy-marker")
    server = _create_test_candidate_mcp()
    assert server is not None
    with pytest.raises(ToolError) as error:
        asyncio.run(server.call_tool("_execute_candidate_transformation", {
            "input_path": "items.csv", "policy_path": "policy.yaml", "output_path": "output",
            "snapshot_sha256": "0" * 64, "max_total_input_bytes": 8192}))
    message = str(error.value)
    assert "requested_above_limit" in message and "8192 > 1024 bytes" in message
    assert "origin=session" in message
    assert "TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES" in message
    assert "resource_limits.max_total_input_bytes" in message
    assert "fictional-source-marker" not in message and "fictional-policy-marker" not in message
    assert not (tmp_path / "output").exists()


def test_closed_sdk_uses_existing_request_budget(tmp_path, monkeypatch):
    from mcp.server.fastmcp.exceptions import ToolError
    from mcp.server.lowlevel.server import request_ctx
    from mcp.shared.context import RequestContext
    from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp
    from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget

    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS)
    budget.consume_canonical_argument_bytes(DEFAULT_QUERY_WORK_LIMITS.canonical_argument_bytes)
    server = _create_test_candidate_mcp()
    assert server is not None
    context = RequestContext(request_id=1, meta=None, session=None, lifespan_context=None, request=budget)
    token = request_ctx.set(context)
    try:
        with pytest.raises(ToolError) as error:
            asyncio.run(server.call_tool("_execute_candidate_transformation", {
                "input_path": "fictional-secret-marker.csv", "policy_path": "policy.yaml",
                "output_path": "output", "snapshot_sha256": "0" * 64}))
        assert "fictional-secret-marker" not in str(error.value)
        assert "query work budget exceeded for canonical argument bytes" in str(error.value)
        assert not list(tmp_path.iterdir())
    finally:
        request_ctx.reset(token)


@pytest.mark.parametrize("transport", ["sdk", "stdio"])
@pytest.mark.parametrize("stale", [False, True])
def test_closed_sdk_dispatch_publishes_or_rejects_stale_snapshot(tmp_path, monkeypatch, stale, transport):
    from mcp.server.fastmcp.exceptions import ToolError
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
    from test_data_agent.core.transformation_snapshot import SnapshotPart
    from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths
    from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp

    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    source = SnapshotPart("source", "items", b"label\nalpha\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [{"entity": "items", "field": "label",
        "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
        "kind": "inline", "entries": [{"original": ["alpha"], "replacement": ["gamma"]}]}}}]})
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    (tmp_path / "items.csv").write_bytes(source.payload)
    (tmp_path / "behavior.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    request = prepare_csv_review_from_paths(tmp_path / "items.csv", "items", tmp_path,
        "behavior.yaml", max_total_bytes=8192, max_review_bytes=8192, budget=GenerationBudget(5))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    server = _create_test_candidate_mcp()
    assert server is not None
    arguments = {"input_path": "items.csv", "policy_path": "behavior.yaml", "output_path": "output",
        "snapshot_sha256": "0" * 64 if stale else request.snapshot_sha256, "max_output_bytes": 8192}
    if transport == "stdio":
        from datetime import timedelta
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        program = (
            "from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp; "
            "from test_data_agent.mcp_generator_server import _new_transport_work_budget; "
            "from test_data_agent.mcp_generator_transport import run_bounded_generator_mcp; "
            "from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS; "
            "run_bounded_generator_mcp(_create_test_candidate_mcp(), "
            "max_payload_bytes=DEFAULT_QUERY_WORK_LIMITS.raw_transport_payload_bytes, "
            "request_context_factory=_new_transport_work_budget)"
        )

        async def invoke():
            parameters = StdioServerParameters(command=sys.executable, args=["-c", program], env=dict(os.environ))
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=15)) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert [tool.name for tool in tools.tools] == ["_execute_candidate_transformation"]
                    malformed = await session.call_tool("_execute_candidate_transformation", {
                        **arguments, "input_path": {"fictional-secret-marker": "rejected"}})
                    assert malformed.isError
                    assert "fictional-secret-marker" not in malformed.model_dump_json()
                    return await session.call_tool("_execute_candidate_transformation", arguments)

        response = asyncio.run(invoke())
        rendered = response.model_dump_json()
        assert response.isError == stale
        assert "alpha" not in rendered and "gamma" not in rendered
        if stale:
            assert not (tmp_path / "output").exists()
        else:
            assert request.snapshot_sha256 in rendered
            assert (tmp_path / "output" / "dataset.csv").read_bytes() == b"label\ngamma\n"
        assert {name: (tmp_path / name).read_bytes() for name in before} == before
        return
    if stale:
        with pytest.raises(ToolError) as error:
            asyncio.run(server.call_tool("_execute_candidate_transformation", arguments))
        assert "alpha" not in str(error.value) and "gamma" not in str(error.value)
        assert not (tmp_path / "output").exists()
    else:
        result = asyncio.run(server.call_tool("_execute_candidate_transformation", arguments))
        rendered = json.dumps(result, default=lambda item: item.model_dump(mode="json"))
        assert request.snapshot_sha256 in rendered
        assert "alpha" not in rendered and "gamma" not in rendered
        assert (tmp_path / "output" / "dataset.csv").read_bytes() == b"label\ngamma\n"
    assert {name: (tmp_path / name).read_bytes() for name in before} == before


def test_closed_mcp_composition_has_execution_but_no_approval_issuer():
    from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp
    from test_data_agent.mcp_generator_server import generator_mcp_services

    server = _create_test_candidate_mcp()
    assert server is not None
    names = [tool.name for tool in asyncio.run(server.list_tools())]
    assert names == ["_execute_candidate_transformation"]
    assert "_execute_candidate_transformation" not in [tool.__name__ for tool in generator_mcp_services()]


@pytest.mark.parametrize("argument", ["input_path", "policy_path", "output_path", "receipt_path"])
def test_candidate_paths_cannot_escape_workspace(tmp_path, monkeypatch, argument):
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "items.csv").write_text("label\nfictional\n")
    (tmp_path / "policy.yaml").write_text("invalid fixture; must never be parsed")
    (tmp_path / "receipt.json").write_text("invalid fixture; must never be parsed")
    arguments = {"input_path": "items.csv", "policy_path": "policy.yaml",
        "output_path": "output", "receipt_path": "receipt.json", "snapshot_sha256": "0" * 64}
    arguments[argument] = "../fictional-outside-marker"
    with pytest.raises(WorkspacePathError) as error:
        _execute_candidate_transformation(**arguments)
    assert "fictional-outside-marker" not in str(error.value)
    assert not (tmp_path / "output").exists()
