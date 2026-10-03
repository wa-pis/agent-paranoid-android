"""Offline skill-guided installed workflows; fictional inputs, no provider/DB."""

import csv
import json
import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import yaml
import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source


def cli(*arguments, env=None):
    return subprocess.run([sys.executable, "-m", "test_data_agent.cli", *map(str, arguments)],
        capture_output=True, text=True, timeout=30, check=False, env=env)


def skill(name, commands):
    text = " ".join(files("test_data_agent").joinpath("skills", name, "SKILL.md").read_text().split())
    assert "offline" in text and "---" in text
    assert cli("--version").returncode == 0
    for command in commands:
        assert command in text or command in {"transform-execute", "transform-approve"}
        help_result = cli(command, "--help")
        assert help_result.returncode == 0 and help_result.stdout.strip()
    return text


def test_usage_skill_reviewed_spec_seeded_generation_and_validation(tmp_path):
    text = skill("agent-paranoid-android-usage", ("generate", "validate"))
    assert "Already reviewed spec" in text and "does not preserve" in text
    spec = tmp_path / "reviewed.json"
    spec.write_text(json.dumps({"entities": [{"name": "items", "row_count": 3,
        "fields": [{"name": "item_id", "data_type": "integer", "is_identifier": True},
                   {"name": "shade", "data_type": "string"}]}]}))
    for name in ("first", "replay"):
        destination = tmp_path / name
        generated = cli("generate", spec, "--seed", "72", "--format", "csv",
            "--output", destination, "--json")
        assert generated.returncode == 0
        assert cli("validate", spec, destination, "--json").returncode == 0
        manifest = json.loads((destination / "generation_manifest.json").read_text())
        assert manifest["synthetic"] and manifest["source_rows_copied"] is False
        assert len(list(csv.DictReader((destination / "items.csv").open()))) == 3
    assert (tmp_path / "first/items.csv").read_bytes() == (tmp_path / "replay/items.csv").read_bytes()


def test_transformation_skill_review_execute_and_no_agent_receipt(tmp_path):
    text = skill("agent-paranoid-android-transformation",
        ("transform-review", "transform-execute", "transform-approve"))
    assert "neither may create the receipt" in text and "do not approximate" in text.lower()
    source = SnapshotPart("source", "items", b"shade,rank\nindigo,2\n")
    data = {"schema_version": "0.1", "seed": 72, "schema_fingerprint": "0" * 64,
        "fields": [{"entity": "items", "field": field, "sensitivity": "non_sensitive",
            "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                {"original": [old], "replacement": [new]}]}}}
            for field, old, new in (("shade", "indigo", "olive"), ("rank", 2, 7))]}
    policy = BehaviorPolicy.model_validate(data)
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    data["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    input_path, policy_path = tmp_path / "items.csv", tmp_path / "behavior.yaml"
    input_path.write_bytes(source.payload)
    policy_path.write_text(yaml.safe_dump(data))
    reviewed = cli("transform-review", input_path, policy_path)
    assert reviewed.returncode == 0
    digest = json.loads(reviewed.stdout)["snapshot_sha256"]
    output = tmp_path / "transformed"
    completed = cli("transform-execute", input_path, policy_path, output,
        "--snapshot-sha256", digest, "--json")
    assert completed.returncode == 0
    assert (output / "dataset.csv").read_bytes() == b"shade,rank\nolive,7\n"
    assert all(value not in reviewed.stdout + completed.stdout for value in ("indigo", "olive"))
    data["fields"][0]["behavior"] = {"action": "preserve", "authorization_ref": "fictional",
        "comment": "Fictional reviewed business shade"}
    policy_path.write_text(yaml.safe_dump(data))
    reviewed = cli("transform-review", input_path, policy_path)
    assert reviewed.returncode == 0
    refusal = cli("transform-execute", input_path, policy_path, tmp_path / "unapproved",
        "--snapshot-sha256", json.loads(reviewed.stdout)["snapshot_sha256"], "--json")
    assert refusal.returncode != 0 and not (tmp_path / "unapproved").exists()
    assert not list(tmp_path.glob("*receipt*"))


def test_transformation_skill_unavailable_baseline_stops_without_substitution(tmp_path):
    # Actual installed baseline, no patched parser or fake command inventory.
    if "APA_SKILL_BASELINE" not in os.environ:
        pytest.skip("actual installed baseline must be provided; no simulated unavailable interface")
    baseline = Path(os.environ["APA_SKILL_BASELINE"])
    assert baseline.joinpath("test_data_agent").is_dir()
    environment = {**os.environ, "PYTHONPATH": str(baseline)}
    unavailable = cli("transform-execute", "--help", env=environment)
    assert unavailable.returncode == 2
    # Guided caller stops here: no fallback generation, receipt or output.
    assert list(tmp_path.iterdir()) == []
