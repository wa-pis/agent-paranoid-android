"""Read-only fictional CSV transformation review through the public CLI."""

import json

import yaml

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.cli import main
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.csv_profiler import profile_csv_bytes


def test_transform_review_uses_fixed_csv_and_local_mapping_without_values(tmp_path, capsys):
    source = tmp_path / "items.csv"
    source.write_bytes(b"status\nready\nwaiting\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.read_bytes(), "items", budget=GenerationBudget(5),
    ))
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "status",
              "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
              "kind": "csv", "path": "map.csv", "source_columns": ["old"],
              "replacement_columns": ["new"]}}}]}
    (tmp_path / "policy.yaml").write_text(yaml.safe_dump(policy))
    (tmp_path / "map.csv").write_bytes(b"old,new\nready,done\nwaiting,pending\n")

    assert main(["transform-review", str(source), str(tmp_path / "policy.yaml"), "--json"]) == 0
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert result["result"]["status"] == "review_only"
    assert result["result"]["review"]["fields"][0]["system_comment"]
    assert len(result["result"]["snapshot_sha256"]) == 64
    assert output.err == ""
    assert "ready" not in output.out
    assert "done" not in output.out
    assert not (tmp_path / "approval.json").exists()


def test_transform_review_rejects_wrong_policy_without_source_values(tmp_path, capsys):
    source = tmp_path / "items.csv"
    source.write_bytes(b"status\nfictional-private-marker\n")
    (tmp_path / "policy.yaml").write_text("schema_version: '0.1'\nfields: []\n")
    assert main(["transform-review", str(source), str(tmp_path / "policy.yaml")]) != 0
    output = capsys.readouterr()
    assert "fictional-private-marker" not in output.out + output.err
