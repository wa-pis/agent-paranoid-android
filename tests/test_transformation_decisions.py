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


@pytest.mark.parametrize("extra", [[], ["--edit-actions"], ["--trace"]])
def test_decisions_reject_piped_input_without_changing_policy(tmp_path, extra):
    source, path, _ = draft(tmp_path)
    before = path.read_bytes()
    result = subprocess.run(command(source, path) + extra, input=b"non_sensitive\nsensitive\nSAVE\n",
                            capture_output=True, env=environment(), timeout=10)
    assert result.returncode != 0
    assert path.read_bytes() == before


def test_action_editor_requires_decision_wizard(tmp_path):
    source, path, _ = draft(tmp_path)
    before = path.read_bytes()
    args = [arg for arg in command(source, path) if arg != "--decide"]
    result = subprocess.run(args + ["--edit-actions"], capture_output=True,
                            env=environment(), timeout=10)
    assert result.returncode != 0
    assert path.read_bytes() == before


@pytest.mark.parametrize(("action", "mapping_kind", "fallback"), [
    (action, "csv", "reject") for action in
    ["keep", "drop", "preserve", "synthesize", "derive", "substitute", "replace_text"]
] + [("substitute", "inline", "preserve"), ("substitute", "inline", "synthesize"),
     ("replace_text", "global", "reject"), ("replace_text", "drift", "reject")])
def test_action_selection_saves_same_versioned_policy(tmp_path, action, mapping_kind, fallback):
    source, path, original = draft(tmp_path)
    (tmp_path / "status.csv").write_bytes(b"old,new\nready,fictional-new-status\n")
    (tmp_path / "generator.yaml").write_text("version: '1.0'\nentities: []\n")
    mapping = {"kind": "csv", "path": "status.csv", "source_columns": ["old"],
               "replacement_columns": ["new"]}
    if mapping_kind == "inline":
        mapping = {"kind": "inline", "entries": [
            {"original": ["ready"], "replacement": ["fictional-new-status"]},
        ]}
    elif mapping_kind == "global":
        original["file_text_mapping"] = mapping
        path.write_text(yaml.safe_dump(original))
        mapping = None
    before = path.read_bytes()
    expected = {"action": "drop" if action == "keep" else action}
    answers = []
    if action == "preserve":
        expected.update(authorization_ref="fictional-auth", comment="fictional-private-comment")
        answers = [(b"Authorization reference (hidden): ", b"fictional-auth"),
                   (b"Preservation comment (hidden): ", b"fictional-private-comment")]
    elif action == "synthesize":
        expected["generation_policy_ref"] = "generator.yaml"
        answers = [(b"Generation policy path (hidden): ", b"generator.yaml")]
    elif action == "derive":
        expected.update(expression="code", dependencies=["code"])
        answers = [(b"Expression (hidden): ", b"code"),
                   (b"Dependency names JSON (hidden): ", b'["code"]')]
    elif action in {"substitute", "replace_text"}:
        unmatched = {"action": fallback}
        expected.update(mapping=mapping, unmatched=unmatched)
        answers = [(b"Mapping JSON (hidden): ", json.dumps(mapping).encode()),
                   (b"Unmatched [reject/preserve/synthesize]: ", fallback.encode())]
        if fallback == "preserve":
            unmatched.update(authorization_ref="fictional-auth", comment="fictional-private-comment")
            answers.extend([(b"Authorization reference (hidden): ", b"fictional-auth"),
                            (b"Preservation comment (hidden): ", b"fictional-private-comment")])
        elif fallback == "synthesize":
            unmatched["generation_policy_ref"] = "generator.yaml"
            answers.append((b"Generation policy path (hidden): ", b"generator.yaml"))
    master, slave = pty.openpty()
    process = subprocess.Popen(command(source, path) + ["--edit-actions"], stdin=slave,
                               stderr=slave, stdout=subprocess.PIPE, env=environment())
    os.close(slave)
    transcript = b""
    try:
        for marker, answer in [
            (b"Decision [sensitive/non_sensitive/unknown]: ", b"non_sensitive"),
            (b"Action [keep/drop/preserve/synthesize/substitute/replace_text/derive]: ", action.encode()),
            *answers,
            (b"Decision [sensitive/non_sensitive/unknown]: ", b"sensitive"),
            (b"Action [keep/drop/preserve/synthesize/substitute/replace_text/derive]: ", b"keep"),
            (b"Type SAVE to replace the policy (not approval): ", b"SAVE"),
        ]:
            transcript += read_until(master, marker)
            if mapping_kind == "drift" and answer == b"SAVE":
                (tmp_path / "status.csv").write_bytes(b"old,new\nready,other-value\n")
            os.write(master, answer + b"\n")
        stdout, _ = process.communicate(timeout=10)
        if mapping_kind == "drift":
            assert process.returncode != 0
            assert path.read_bytes() == before
            return
        assert process.returncode == 0, stdout
        original["fields"][0].update(sensitivity="non_sensitive", behavior=expected)
        original["fields"][1]["sensitivity"] = "sensitive"
        assert parse_behavior_policy(yaml.safe_load(path.read_bytes())) == parse_behavior_policy(original)
        assert b"fictional-private-comment" not in transcript + stdout
        assert b"fictional-auth" not in transcript + stdout
        assert b"fictional-new-status" not in transcript + stdout
        assert b"fictional-A" not in transcript + stdout
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
@pytest.mark.parametrize("expression", ["missing + 1", "count()", "evil('fictional-private-expression')"])
def test_action_editor_rejects_invalid_derived_expression_without_saving(tmp_path, expression):
    source, path, _ = draft(tmp_path)
    before = path.read_bytes()
    master, slave = pty.openpty()
    process = subprocess.Popen(command(source, path) + ["--edit-actions"], stdin=slave,
                               stderr=slave, stdout=subprocess.PIPE, env=environment())
    os.close(slave)
    transcript = b""
    try:
        for marker, answer in [
            (b"Decision [sensitive/non_sensitive/unknown]: ", b"non_sensitive"),
            (b"Action [keep/drop/preserve/synthesize/substitute/replace_text/derive]: ", b"derive"),
            (b"Expression (hidden): ", expression.encode()),
            (b"Dependency names JSON (hidden): ", b'["code"]'),
            (b"Decision [sensitive/non_sensitive/unknown]: ", b"sensitive"),
            (b"Action [keep/drop/preserve/synthesize/substitute/replace_text/derive]: ", b"keep"),
        ]:
            transcript += read_until(master, marker)
            os.write(master, answer + b"\n")
        stdout, _ = process.communicate(timeout=10)
        assert process.returncode != 0
        assert path.read_bytes() == before
        assert b"fictional-private-expression" not in transcript + stdout
        assert b"fictional-A" not in transcript + stdout
        assert b"Type SAVE" not in transcript
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
