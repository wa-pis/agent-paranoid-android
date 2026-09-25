"""Exercise the decision wizard through a real CLI and fictional local files."""

import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import time

import pytest
import yaml

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import parse_behavior_policy, transformation_schema_fingerprint
from test_data_agent.csv_profiler import profile_csv_bytes


def draft(tmp_path):
    source = tmp_path / "items.csv"
    source.write_bytes(b"status,code\nready,fictional-A\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.read_bytes(), "items", budget=GenerationBudget(),
    ))
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [
                  {"entity": "items", "field": "status", "sensitivity": "unknown",
                   "behavior": {"action": "drop"}},
                  {"entity": "items", "field": "code", "sensitivity": "unknown",
                   "behavior": {"action": "replace_text", "mapping": {
                       "kind": "csv", "path": "map.csv", "source_columns": ["old"],
                       "replacement_columns": ["new"]}}},
              ]}
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(policy))
    (tmp_path / "map.csv").write_bytes(b"old,new\nfictional-A,fictional-B\n")
    return source, path, policy


def command(source, policy):
    return [sys.executable, "-m", "test_data_agent.cli", "transform-review", str(source),
            str(policy), "--decide", "--json"]


def environment():
    return {**os.environ, "PYTHONPATH": str(Path("src").resolve())}


def read_until(fd, marker):
    result = bytearray()
    deadline = time.monotonic() + 10
    while marker not in result:
        assert time.monotonic() < deadline, "CLI prompt timed out"
        if select.select([fd], [], [], 0.1)[0]:
            chunk = os.read(fd, 65536)
            assert chunk, f"CLI closed before prompt: {bytes(result)!r}"
            result.extend(chunk)
    return bytes(result)


@pytest.mark.parametrize("failure", [None, "cancel", "source", "mapping", "policy", "conflict", "empty"])
def test_decision_wizard_roundtrip_or_atomic_failure(tmp_path, failure):
    source, path, original = draft(tmp_path)
    if failure == "conflict":
        original["fields"][0].update(sensitivity="non_sensitive", behavior={
            "action": "preserve", "authorization_ref": "fictional-local-ref",
            "comment": "Fictional business status reviewed locally.",
        })
        path.write_text(yaml.safe_dump(original))
    before = path.read_bytes()
    master, slave = pty.openpty()
    process = subprocess.Popen(command(source, path), stdin=slave, stderr=slave,
                               stdout=subprocess.PIPE, env=environment())
    os.close(slave)
    try:
        transcript = read_until(master, b"Decision [sensitive/non_sensitive/unknown]: ")
        assert b"system_comment" in transcript
        assert b"observed_sensitivity" in transcript
        if failure == "empty":
            os.write(master, b"\n")
            stdout, _ = process.communicate(timeout=10)
            assert process.returncode != 0
            assert path.read_bytes() == before
            assert b"fictional-A" not in stdout
            return
        os.write(master, b"sensitive\n" if failure == "conflict" else b"non_sensitive\n")
        transcript += read_until(master, b"Decision [sensitive/non_sensitive/unknown]: ")
        os.write(master, b"sensitive\n")
        if failure != "conflict":
            transcript += read_until(master, b"Type SAVE to replace the policy (not approval): ")
            if failure in {"source", "mapping", "policy"}:
                target = {"source": source, "mapping": tmp_path / "map.csv", "policy": path}[failure]
                target.write_bytes(target.read_bytes() + b"\n")
                if failure == "policy":
                    before = path.read_bytes()
            os.write(master, b"CANCEL\n" if failure == "cancel" else b"SAVE\n")
        stdout, _ = process.communicate(timeout=10)
        assert b"fictional-A" not in transcript + stdout
        assert b"fictional-B" not in transcript + stdout
        assert not (tmp_path / "approval.json").exists()
        if failure:
            assert process.returncode != 0
            assert path.read_bytes() == before
        else:
            assert process.returncode == 0, stdout
            result = json.loads(stdout)["result"]
            assert result["status"] == "policy_saved"
            expected = original
            expected["fields"][0]["sensitivity"] = "non_sensitive"
            expected["fields"][1]["sensitivity"] = "sensitive"
            assert parse_behavior_policy(yaml.safe_load(path.read_bytes())) == parse_behavior_policy(expected)
            assert path.stat().st_mode & 0o077 == 0
            review = subprocess.run(command(source, path)[:-2] + ["--json"],
                                    capture_output=True, env=environment(), timeout=10)
            assert review.returncode == 0
            assert json.loads(review.stdout)["result"]["review"] == result["review"]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


def test_decisions_reject_piped_input_without_changing_policy(tmp_path):
    source, path, _ = draft(tmp_path)
    before = path.read_bytes()
    result = subprocess.run(command(source, path), input=b"non_sensitive\nsensitive\nSAVE\n",
                            capture_output=True, env=environment(), timeout=10)
    assert result.returncode != 0
    assert path.read_bytes() == before
