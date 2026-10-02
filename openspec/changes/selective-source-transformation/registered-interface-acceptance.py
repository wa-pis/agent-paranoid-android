"""Explicit fictional acceptance for an isolated registration candidate only.

Run pytest on this file with candidate-only PYTHONPATH and -o pythonpath=.
Never patches product guards; no DB/API connections.
"""
import asyncio
import json
import os
import subprocess
import sys
import pty
import select
import time
from datetime import timedelta
from pathlib import Path

import yaml
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source


def test_registered_contract_delta(tmp_path):
    from scripts.contract_fixtures import build_contract_fixtures

    actual = build_contract_fixtures(tmp_path)
    candidate_inventories = json.loads(Path(__file__).with_name(
        "activation-contract-inventories.json").read_text())
    assert {name: actual[name] for name in candidate_inventories} == candidate_inventories
    expected = {name: json.loads((Path("tests/fixtures/contracts") / name).read_text())
                for name in actual}
    parser = actual["cli-parser-surface.json"]
    added_commands = {"transform-execute", "transform-approve"}
    assert added_commands <= set(parser["commands"])
    parser["commands"] = [name for name in parser["commands"] if name not in added_commands]
    tools = actual["mcp-generator-tools.json"]
    added = [tool for tool in tools if tool["name"] == "execute_transformation"]
    assert len(added) == 1
    schema = added[0]["input_schema"]
    assert set(schema["required"]) == {
        "input_path", "policy_path", "output_path", "snapshot_sha256"}
    assert set(schema["properties"]) == {
        "input_path", "policy_path", "output_path", "snapshot_sha256", "table_name",
        "receipt_path", "max_total_input_bytes", "max_output_bytes"}
    assert "approved" not in schema["properties"]
    actual["mcp-generator-tools.json"] = [tool for tool in tools
                                         if tool["name"] != "execute_transformation"]
    assert actual == expected


@pytest.mark.parametrize("preserve", [False, True])
def test_registered_profile_review_execution(tmp_path, preserve):
    source = SnapshotPart("source", "items", b"label\nalpha\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [{"entity": "items", "field": "label",
        "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
        "kind": "inline", "entries": [{"original": ["alpha"], "replacement": ["gamma"]}]}}}]})
    if preserve:
        source = SnapshotPart("source", "items", b"code,label\nfictional-a,alpha\n")
        data = policy.model_dump(mode="json")
        data["fields"].insert(0, {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
            "behavior": {"action": "preserve", "authorization_ref": "fictional-local",
                         "comment": "Reviewed fictional business code"}})
        policy = BehaviorPolicy.model_validate(data)
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    input_path = tmp_path / "items.csv"
    policy_path = tmp_path / "behavior.yaml"
    input_path.write_bytes(source.payload)
    policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    before = (input_path.read_bytes(), policy_path.read_bytes())

    def cli(*arguments):
        response = subprocess.run([sys.executable, "-c",
            "import sys; from test_data_agent.cli import main; sys.exit(main())", *arguments],
            capture_output=True, text=True, timeout=15)
        assert response.returncode == 0, response.stderr
        assert "alpha" not in response.stdout + response.stderr
        assert "gamma" not in response.stdout + response.stderr
        assert "fictional-a" not in response.stdout + response.stderr
        return json.loads(response.stdout)["result"]

    review = cli("transform-review", str(input_path), str(policy_path), "--json")
    digest = review["snapshot_sha256"]
    receipt_arguments = []
    if preserve:
        program = ("import fcntl,termios,os,sys; fcntl.ioctl(0,termios.TIOCSCTTY,0); "
            "os.tcsetpgrp(0,os.getpgrp()); from test_data_agent.cli import main; sys.exit(main())")
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, "-c", program, "transform-approve",
            str(input_path), str(policy_path), str(tmp_path / "receipt.json"),
            "--snapshot-sha256", digest, "--json"],
            stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave)
        transcript = bytearray()
        try:
            deadline = time.monotonic() + 15
            while b"Type APPROVE" not in transcript:
                assert time.monotonic() < deadline and process.poll() is None, bytes(transcript)
                if select.select([master], [], [], 0.1)[0]:
                    transcript.extend(os.read(master, 16384))
            assert b"fictional-a" not in transcript and b"alpha" not in transcript
            os.write(master, b"APPROVE\n")
            while process.poll() is None:
                assert time.monotonic() < deadline, bytes(transcript)
                if select.select([master], [], [], 0.1)[0]:
                    transcript.extend(os.read(master, 16384))
            assert process.returncode == 0, bytes(transcript)
        finally:
            os.close(master)
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
        assert (tmp_path / "receipt.json").stat().st_mode & 0o077 == 0
        receipt_arguments = ["--receipt", str(tmp_path / "receipt.json")]
    result = cli("transform-execute", str(input_path), str(policy_path), str(tmp_path / "cli-output"),
        "--snapshot-sha256", digest, "--max-output-bytes", "8192", "--json", *receipt_arguments)
    assert result["status"] == "transformation_completed" and result["snapshot_sha256"] == digest
    if preserve:
        rejected_commands = [
            ["transform-approve", str(input_path), str(policy_path), str(tmp_path / "detached.json"),
             "--snapshot-sha256", digest],
            ["transform-execute", str(input_path), str(policy_path), str(tmp_path / "rejected-output"),
             "--snapshot-sha256", digest],
            ["transform-execute", str(input_path), str(policy_path), str(tmp_path / "rejected-output"),
             "--snapshot-sha256", "0" * 64, *receipt_arguments],
        ]
        for command in rejected_commands:
            rejected = subprocess.run([sys.executable, "-c",
                "import sys; from test_data_agent.cli import main; sys.exit(main())",
                *command, "--json"], input="APPROVE\n", capture_output=True, text=True,
                timeout=15, start_new_session=True)
            assert rejected.returncode != 0
            assert json.loads(rejected.stdout)["error"]["exit_code"] == rejected.returncode
            assert all(value not in rejected.stdout + rejected.stderr for value in
                       ("alpha", "gamma", "fictional-a"))
            assert not (tmp_path / "detached.json").exists()
            assert not (tmp_path / "rejected-output").exists()

    async def invoke():
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "test_data_agent.mcp_generator_server"],
            env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path)})
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=15)) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert "execute_transformation" in {tool.name for tool in tools.tools}
                assert "transform-approve" not in {tool.name for tool in tools.tools}
                arguments = {
                    "input_path": "items.csv", "policy_path": "behavior.yaml",
                    "output_path": "mcp-output", "snapshot_sha256": digest, "max_output_bytes": 8192,
                    **({"receipt_path": "receipt.json"} if preserve else {})}
                if preserve:
                    (tmp_path / "forged.json").write_text('{"approved":true,"fictional-secret-marker":"fake"}')
                    changes = [
                        {"receipt_path": None}, {"receipt_path": "forged.json"},
                        {"receipt_path": None, "approved": True},
                        {"snapshot_sha256": "0" * 64},
                        {"output_path": "../fictional-secret-marker"},
                        {"input_path": {"fictional-secret-marker": "invalid"}},
                        {"max_output_bytes": 1 << 63},
                        {"output_path": "cli-output"},
                    ]
                    receipt_before = (tmp_path / "receipt.json").read_bytes()
                    cli_before = (tmp_path / "cli-output" / "dataset.csv").read_bytes()
                    for change in changes:
                        rejected = await session.call_tool("execute_transformation", {**arguments, **change})
                        assert rejected.isError
                        rendered = rejected.model_dump_json()
                        assert all(value not in rendered for value in
                                   ("alpha", "gamma", "fictional-a", "fictional-secret-marker"))
                        assert not (tmp_path / "mcp-output").exists()
                        assert (tmp_path / "receipt.json").read_bytes() == receipt_before
                        assert (tmp_path / "cli-output" / "dataset.csv").read_bytes() == cli_before
                    for path, original, modified in (
                        (input_path, before[0], before[0].replace(b"fictional-a", b"fictional-b")),
                        (policy_path, before[1], before[1].replace(b"gamma", b"delta")),
                    ):
                        try:
                            path.write_bytes(modified)
                            changed = cli("transform-review", str(input_path), str(policy_path), "--json")
                            assert changed["snapshot_sha256"] != digest
                            rejected = await session.call_tool("execute_transformation", {
                                **arguments, "snapshot_sha256": changed["snapshot_sha256"]})
                            assert rejected.isError
                            assert all(value not in rejected.model_dump_json() for value in
                                       ("alpha", "gamma", "delta", "fictional-a", "fictional-b"))
                            assert not (tmp_path / "mcp-output").exists()
                            assert (tmp_path / "receipt.json").read_bytes() == receipt_before
                            assert (tmp_path / "cli-output" / "dataset.csv").read_bytes() == cli_before
                        finally:
                            path.write_bytes(original)
                return await session.call_tool("execute_transformation", arguments)

    response = asyncio.run(invoke())
    assert not response.isError
    assert "alpha" not in response.model_dump_json() and "gamma" not in response.model_dump_json()
    assert "fictional-a" not in response.model_dump_json()
    assert digest in response.model_dump_json()
    for name in ("cli-output", "mcp-output"):
        expected = b"code,label\nfictional-a,gamma\n" if preserve else b"label\ngamma\n"
        assert (tmp_path / name / "dataset.csv").read_bytes() == expected
    assert before == (input_path.read_bytes(), policy_path.read_bytes())
