"""Fictional private CLI composition; production commands stay unregistered."""

import json
import argparse
import errno
import os
import pty
import select
import subprocess
import sys
import time

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths


def test_closed_prospective_parser_has_explicit_execution_and_no_approval():
    from test_data_agent.cli_transformation_candidate import _create_test_execution_parser

    parser = _create_test_execution_parser()
    arguments = parser.parse_args(["transform-execute", "source.csv", "policy.yaml", "output",
        "--snapshot-sha256", "0" * 64, "--json", "--max-output-bytes", "8192"])
    assert arguments.command == "transform-execute" and arguments.json_output
    assert arguments.max_output_bytes == 8192 and arguments.receipt is None
    assert "transform-approve" not in parser.format_help()


@pytest.mark.parametrize("failure", ["missing_digest", "invalid_cap"])
def test_closed_prospective_dispatch_requires_review_digest(tmp_path, capsys, failure):
    from test_data_agent.cli_transformation_candidate import _candidate_execution_main

    arguments = ["transform-execute", "fictional-secret-marker.csv", "policy.yaml",
                 str(tmp_path / "output"), "--json"]
    if failure == "invalid_cap":
        arguments.extend(["--snapshot-sha256", "0" * 64, "--max-output-bytes", "fictional-secret-marker"])
    with pytest.raises(SystemExit) as error:
        _candidate_execution_main(arguments, prospective=True)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["error"]["code"] == "invalid_arguments"
    assert "fictional-secret-marker" not in captured.out + captured.err
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mode", ["malformed", "missing", "limit"])
def test_closed_entrypoint_returns_safe_json_failure(tmp_path, mode):
    program = ("import sys; from test_data_agent.cli_transformation_candidate import "
        "_candidate_execution_main; sys.exit(_candidate_execution_main(sys.argv[1:], json_output=True))")
    source = tmp_path / "source.csv"
    policy = tmp_path / "policy.yaml"
    if mode == "limit":
        source.write_text("label\nfictional-secret-marker\n")
        policy.write_text("fictional-secret-marker")
    arguments = [str(source), str(policy), str(tmp_path / "output"), "--snapshot-sha256", "0" * 64]
    if mode == "malformed":
        arguments += ["--max-total-input-bytes", "fictional-secret-marker"]
    elif mode == "limit":
        arguments += ["--max-total-input-bytes", "8192"]
    result = subprocess.run([sys.executable, "-c", program, *arguments], capture_output=True,
        text=True, timeout=15, env={**os.environ, "TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES": "1024"})
    assert result.returncode == 2
    document = json.loads(result.stdout)
    assert document["ok"] is False
    assert not result.stderr
    assert "fictional-secret-marker" not in result.stdout
    if mode == "limit":
        assert "requested_above_limit" in document["error"]["message"]
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("failure", ["limit", "cleanup"])
def test_existing_cli_presenter_preserves_transformation_recovery(capsys, json_output, failure):
    from test_data_agent.cli_contract import CliErrorCode
    from test_data_agent.cli_presenter import friendly_error, report_cli_error
    from test_data_agent.core.transformation_limits import InputDimension, TransformationLimitError
    from test_data_agent.io.transformation_publish import TransformationCleanupError

    error = (TransformationLimitError(InputDimension.TOTAL_BYTES, 8192, 1024,
        "session", requested=True) if failure == "limit" else
        TransformationCleanupError("transformation cleanup incomplete; output or staging may remain"))
    args = argparse.Namespace(command="closed-transform-execute", json_output=json_output)
    assert report_cli_error(args, code=CliErrorCode.INVALID_INPUT, message=friendly_error(error)) == 2
    captured = capsys.readouterr()
    if json_output:
        document = json.loads(captured.out)
        message = document["error"]["message"]
        assert document["ok"] is False
        assert not captured.err
    else:
        message = captured.err
    if failure == "limit":
        assert "requested_above_limit" in message and "8192 > 1024 bytes" in message
        assert "origin=session" in message and "resource_limits.max_total_input_bytes" in message
    else:
        assert "cleanup incomplete" in message and "may remain" in message
    if not json_output:
        assert not captured.out


@pytest.mark.parametrize("function", ["_run_candidate_execution", "_run_candidate_local_approval"])
@pytest.mark.parametrize("invalid", ["integer", "unknown"])
def test_candidate_parser_rejects_without_reflecting_arguments(tmp_path, function, invalid):
    program = (f"import sys; from test_data_agent.cli_transformation_candidate import {function}; "
        f"{function}(sys.argv[1:])")
    arguments = ["source.csv", "policy.yaml", str(tmp_path / "output"),
        "--snapshot-sha256", "0" * 64]
    arguments += (["--max-total-input-bytes", "fictional-secret-marker"] if invalid == "integer"
                  else ["--fictional-secret-marker"])
    result = subprocess.run([sys.executable, "-c", program, *arguments],
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "invalid transformation arguments" in result.stderr
    assert "fictional-secret-marker" not in result.stdout + result.stderr
    assert "--help" in result.stderr
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("entrance", ["approval", "execution", "workspace"])
def test_candidate_entrances_reject_private_derive_before_artifacts(tmp_path, entrance):
    source = SnapshotPart("source", "items", b"amount,total\n12,24\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [
        {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
         "behavior": {"action": "substitute", "mapping": {"kind": "inline",
          "entries": [{"original": [12], "replacement": [13]}]}}},
        {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
         "behavior": {"action": "derive", "expression": "amount * 2", "dependencies": ["amount"]}}]})
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    (tmp_path / "items.csv").write_bytes(source.payload)
    (tmp_path / "behavior.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    request = prepare_csv_review_from_paths(tmp_path / "items.csv", "items", tmp_path,
        "behavior.yaml", max_total_bytes=8192, max_review_bytes=8192, budget=GenerationBudget(5))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    if entrance == "workspace":
        program = ("import sys; from test_data_agent.mcp_transformation_candidate import "
            "_execute_candidate_transformation; _execute_candidate_transformation("
            "'items.csv','behavior.yaml','output',sys.argv[1])")
        arguments = [request.snapshot_sha256]
    else:
        function = "_run_candidate_local_approval" if entrance == "approval" else "_run_candidate_execution"
        program = (f"import sys; from test_data_agent.cli_transformation_candidate import {function}; "
            f"{function}(sys.argv[1:])")
        arguments = [str(tmp_path / "items.csv"), str(tmp_path / "behavior.yaml"),
            str(tmp_path / ("receipt.json" if entrance == "approval" else "output")),
            "--snapshot-sha256", request.snapshot_sha256]
    env = {**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path)}
    result = subprocess.run([sys.executable, "-c", program, *arguments], env=env,
        capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert "unsupported transformation execution action" in result.stderr if entrance == "approval" else (
        "invalid temporary transformation command" in result.stderr)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


@pytest.mark.parametrize("mode", ["prospective", "entrypoint", "explicit", "stale", "profile", "session", "above_session",
    "total_above", "total_exceeded"])
def test_saved_policy_review_to_candidate_cli_subprocess(tmp_path, mode):
    source = SnapshotPart("source", "items", b"label\nalpha\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [{"entity": "items", "field": "label",
        "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
        "kind": "inline", "entries": [{"original": ["alpha"], "replacement": ["gamma"]}]}}}]})
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    if mode == "profile":
        policy = BehaviorPolicy.model_validate({**policy.model_dump(mode="json"),
            "resource_limits": {"max_output_bytes": 8192, "max_total_input_bytes": 8192}})
    (tmp_path / "items.csv").write_bytes(source.payload)
    (tmp_path / "behavior.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    request = prepare_csv_review_from_paths(tmp_path / "items.csv", "items", tmp_path,
        "behavior.yaml", max_total_bytes=8192, max_review_bytes=8192, budget=GenerationBudget(5))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    program = ("import json,sys; from test_data_agent.cli_transformation_candidate import "
        "_run_candidate_execution; print(json.dumps(_run_candidate_execution(sys.argv[1:])))")
    if mode == "entrypoint":
        program = ("import sys; from test_data_agent.cli_transformation_candidate import "
            "_candidate_execution_main; sys.exit(_candidate_execution_main(sys.argv[1:], json_output=True))")
    if mode == "prospective":
        program = ("import sys; from test_data_agent.cli_transformation_candidate import "
            "_candidate_execution_main; sys.exit(_candidate_execution_main(sys.argv[1:], "
            "json_output=True, prospective=True))")
    argv = [sys.executable, "-c", program, str(tmp_path / "items.csv"),
        str(tmp_path / "behavior.yaml"), str(tmp_path / "output"), "--snapshot-sha256",
        "0" * 64 if mode == "stale" else request.snapshot_sha256]
    if mode == "prospective":
        argv.insert(3, "transform-execute")
    if mode not in {"profile", "session"}:
        argv += ["--max-output-bytes", "8192"]
    env = dict(os.environ)
    if mode in {"session", "above_session"}:
        env["TEST_DATA_AGENT_TRANSFORM_MAX_OUTPUT_BYTES"] = "8192" if mode == "session" else "4096"
        env["TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES"] = "8192"
    if mode in {"total_above", "total_exceeded"}:
        env["TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES"] = "1024"
        if mode == "total_above":
            argv += ["--max-total-input-bytes", "8192"]
    result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=15)
    if mode in {"stale", "above_session", "total_above", "total_exceeded"}:
        assert result.returncode != 0
        assert not (tmp_path / "output").exists()
        if mode == "above_session":
            assert "requested_above_limit" in result.stderr
            assert "origin=session" in result.stderr
        if mode in {"total_above", "total_exceeded"}:
            assert ("requested_above_limit" if mode == "total_above" else "limit_exceeded") in result.stderr
            assert "max_total_input_bytes" in result.stderr
            assert "origin=session" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["snapshot_sha256"] == request.snapshot_sha256
        if mode in {"profile", "session"}:
            assert json.loads(result.stdout)["output_budget"] == {
                "run_bytes": 8192, "ceiling_bytes": 8192, "ceiling_origin": mode}
        assert (tmp_path / "output" / "dataset.csv").read_bytes() == b"label\ngamma\n"
    assert "alpha" not in result.stdout + result.stderr
    assert {name: (tmp_path / name).read_bytes() for name in before} == before


def test_local_candidate_tty_receipt_to_execution(tmp_path):
    from test_data_agent.io.transformation_receipt import _canonical_request
    source = SnapshotPart("source", "items", b"code,label\nfictional-a,alpha\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [
        {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
         "behavior": {"action": "preserve", "authorization_ref": "fictional-local",
                      "comment": "Reviewed fictional business code"}},
        {"entity": "items", "field": "label", "sensitivity": "non_sensitive",
         "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
             {"original": ["alpha"], "replacement": ["gamma"]}]}}}]})
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    (tmp_path / "items.csv").write_bytes(source.payload)
    (tmp_path / "behavior.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    request = prepare_csv_review_from_paths(tmp_path / "items.csv", "items", tmp_path,
        "behavior.yaml", max_total_bytes=8192, max_review_bytes=8192, budget=GenerationBudget(5))
    assert _canonical_request(request, max_total_bytes=8192, max_review_bytes=8192,
        budget=GenerationBudget(5)) == request
    program = ("import fcntl,termios,json,sys,os; fcntl.ioctl(0,termios.TIOCSCTTY,0); "
        "os.tcsetpgrp(0,os.getpgrp()); "
        "from test_data_agent.cli_transformation_candidate import _run_candidate_local_approval; "
        "print(json.dumps(_run_candidate_local_approval(sys.argv[1:])))")
    master, slave = pty.openpty()
    process = subprocess.Popen([sys.executable, "-c", program, str(tmp_path / "items.csv"),
        str(tmp_path / "behavior.yaml"), str(tmp_path / "receipt.json"), "--snapshot-sha256",
        request.snapshot_sha256], stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    os.close(slave)
    transcript = bytearray()
    try:
        deadline = time.monotonic() + 15
        while b"Type APPROVE" not in transcript:
            assert time.monotonic() < deadline, bytes(transcript)
            assert select.select([master], [], [], 1)[0]
            transcript.extend(os.read(master, 16384))
            assert process.poll() is None, bytes(transcript)
        assert b"fictional-a" not in transcript and b"alpha" not in transcript
        os.write(master, b"APPROVE\n")
        # Drain the PTY while waiting: terminal output can otherwise block exit.
        deadline = time.monotonic() + 15
        while process.poll() is None:
            assert time.monotonic() < deadline, bytes(transcript)
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 16384)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    chunk = b""  # Linux PTY EOF after the slave closes.
                if not chunk:
                    process.wait(timeout=max(0.1, deadline - time.monotonic()))
                    break
                transcript.extend(chunk)
        assert process.returncode == 0, bytes(transcript)
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
    receipt = tmp_path / "receipt.json"
    assert receipt.stat().st_mode & 0o077 == 0
    execution = ("import json,sys; from test_data_agent.cli_transformation_candidate import "
        "_run_candidate_execution; print(json.dumps(_run_candidate_execution(sys.argv[1:])))")
    result = subprocess.run([sys.executable, "-c", execution, str(tmp_path / "items.csv"),
        str(tmp_path / "behavior.yaml"), str(tmp_path / "output"), "--snapshot-sha256",
        request.snapshot_sha256, "--receipt", str(receipt), "--max-output-bytes", "8192"],
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "output" / "dataset.csv").read_bytes() == b"code,label\nfictional-a,gamma\n"
    assert "fictional-a" not in result.stdout + result.stderr
    agent = ("import json; from test_data_agent.mcp_transformation_candidate import "
        "_execute_candidate_transformation; print(json.dumps(_execute_candidate_transformation("
        f"'items.csv','behavior.yaml','agent-output',{request.snapshot_sha256!r},"
        "receipt_path='receipt.json',max_output_bytes=8192)))")
    agent_result = subprocess.run([sys.executable, "-c", agent], capture_output=True,
        text=True, timeout=15, env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path)})
    assert agent_result.returncode == 0, agent_result.stderr
    assert json.loads(agent_result.stdout) == json.loads(result.stdout)
    assert (tmp_path / "agent-output" / "dataset.csv").read_bytes() == (
        tmp_path / "output" / "dataset.csv").read_bytes()
    assert "fictional-a" not in agent_result.stdout + agent_result.stderr
    # The same real local receipt must authorize the prospective bounded tool.
    import asyncio
    from datetime import timedelta
    from importlib.metadata import version
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    program = (
        "from test_data_agent.mcp_transformation_candidate import _create_test_candidate_mcp; "
        "from test_data_agent.mcp_generator_server import _new_transport_work_budget; "
        "from test_data_agent.mcp_generator_transport import run_bounded_generator_mcp; "
        "from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS; "
        "run_bounded_generator_mcp(_create_test_candidate_mcp(prospective=True), "
        "max_payload_bytes=DEFAULT_QUERY_WORK_LIMITS.raw_transport_payload_bytes, "
        "request_context_factory=_new_transport_work_budget)")

    async def invoke():
        parameters = StdioServerParameters(command=sys.executable, args=["-c", program],
            env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path)})
        async with stdio_client(parameters) as (reader, writer):
            timeout = 15 if int(version("mcp").split(".")[0]) >= 2 else timedelta(seconds=15)
            async with ClientSession(reader, writer, read_timeout_seconds=timeout) as session:
                await session.initialize()
                return await session.call_tool("execute_transformation", {
                    "input_path": "items.csv", "policy_path": "behavior.yaml",
                    "output_path": "stdio-output", "snapshot_sha256": request.snapshot_sha256,
                    "receipt_path": "receipt.json", "max_output_bytes": 8192})

    response = asyncio.run(invoke())
    assert not response.model_dump(by_alias=True)["isError"]
    assert "fictional-a" not in response.model_dump_json() and "alpha" not in response.model_dump_json()
    assert (tmp_path / "stdio-output" / "dataset.csv").read_bytes() == (
        tmp_path / "output" / "dataset.csv").read_bytes()
    receipt_before = receipt.read_bytes()
    for mode in ("existing", "stale", "no_tty"):
        target = receipt if mode == "existing" else tmp_path / f"{mode}.json"
        approval = ("import json,sys; from test_data_agent.cli_transformation_candidate import "
            "_run_candidate_local_approval; print(json.dumps(_run_candidate_local_approval(sys.argv[1:])))")
        rejected = subprocess.run([sys.executable, "-c", approval,
            str(tmp_path / "items.csv"), str(tmp_path / "behavior.yaml"), str(target),
            "--snapshot-sha256", "0" * 64 if mode == "stale" else request.snapshot_sha256],
            input="APPROVE\n", capture_output=True, text=True, timeout=15,
            start_new_session=True)
        assert rejected.returncode != 0
        assert "fictional-a" not in rejected.stdout + rejected.stderr
        assert receipt.read_bytes() == receipt_before
        if mode != "existing":
            assert not target.exists()

@pytest.mark.parametrize("versioned", [False, True])
def test_common_cli_preserves_cleanup_warning(tmp_path, monkeypatch, capsys, versioned):
    from test_data_agent.cli_transformation_candidate import _candidate_batch_main
    from test_data_agent.io import transformation_batch_workflow
    from test_data_agent.io.transformation_publish import TransformationCleanupError

    def fail(*args, **kwargs):
        raise TransformationCleanupError(
            "transformation publication failed; cleanup incomplete; output or staging may remain; "
            "inspect the selected destination before retrying")

    monkeypatch.setattr(transformation_batch_workflow, "run_batch_workflow", fail)
    assert _candidate_batch_main(["execute", str(tmp_path), "batch.yaml",
        "--max-total-input-bytes", "32768", "--max-review-bytes", "8192",
        "--max-output-bytes", "8192"], versioned_output=versioned) == 2
    captured = capsys.readouterr()
    message = json.loads(captured.out)["error"]["message"]
    assert "cleanup incomplete" in message
    assert "output or staging may remain" in message
    assert "before retrying" in message
    assert not captured.err
