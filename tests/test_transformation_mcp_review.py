"""Read-only MCP parity and workspace boundaries for fictional policy review."""

import json
import os
import selectors
import subprocess
import sys

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths
from test_data_agent.mcp_generator_server import WorkspacePathError, review_transformation


def test_review_matches_shared_request_and_never_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES", "8192")
    source = SnapshotPart("source", "items", b"label\nalpha\nbeta\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "schema_fingerprint": "0" * 64,
        "seed": 7, "fields": [{"entity": "items", "field": "label", "sensitivity": "non_sensitive",
            "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                {"original": ["alpha"], "replacement": ["gamma"]},
                {"original": ["beta"], "replacement": ["delta"]}]}}}]})
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    (tmp_path / "items.csv").write_bytes(source.payload)
    (tmp_path / "behavior.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    request = prepare_csv_review_from_paths(tmp_path / "items.csv", "items", tmp_path,
        "behavior.yaml", max_total_bytes=8192, max_review_bytes=8192, budget=GenerationBudget(5))
    result = review_transformation("items.csv", "behavior.yaml")
    assert result["status"] == "review_only"
    assert result["snapshot_sha256"] == request.snapshot_sha256
    assert result["review"] == json.loads(request.review)
    assert all(value not in json.dumps(result) for value in ("alpha", "beta", "gamma"))
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    # Exercise the real registered tool over SDK stdio, not a patched adapter.
    with (tmp_path / "transport.log").open("w+") as errors:
        process = subprocess.Popen([sys.executable, "-m", "test_data_agent.mcp_generator_server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True,
            env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path)})
        assert process.stdin is not None and process.stdout is not None

        def exchange(message):
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=15), "MCP response deadline exceeded"
            return json.loads(process.stdout.readline())

        try:
            assert "result" in exchange({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                    "clientInfo": {"name": "fictional-review", "version": "1"}}})
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            process.stdin.flush()
            response = exchange({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "review_transformation", "arguments": {
                    "input_path": "items.csv", "policy_path": "behavior.yaml"}}})
            assert not response["result"].get("isError")
            assert json.loads(response["result"]["content"][0]["text"]) == result
            response = exchange({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "review_transformation", "arguments": {
                    "input_path": "../fictional-private-marker", "policy_path": "behavior.yaml"}}})
            assert response["result"]["isError"]
            assert "fictional-private-marker" not in json.dumps(response)
            process.stdin.close()
            assert process.wait(timeout=10) == 0
            errors.seek(0)
            assert "fictional-private-marker" not in errors.read()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
    assert {name: (tmp_path / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("argument", ["input_path", "policy_path"])
def test_review_rejects_paths_outside_workspace(tmp_path, monkeypatch, argument):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "items.csv").write_text("label\nalpha\n")
    (root / "behavior.yaml").write_text("invalid")
    (tmp_path / "outside").write_text("fictional-private-marker")
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(root))
    values = {"input_path": "items.csv", "policy_path": "behavior.yaml", argument: "../outside"}
    with pytest.raises(WorkspacePathError):
        review_transformation(**values)
