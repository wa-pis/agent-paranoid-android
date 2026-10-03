"""Installed public CLI acceptance of linked fields in one fictional input."""
import csv
import json
import subprocess
import sys

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source


@pytest.mark.parametrize("missing", [False, True])
def test_linked_fields_use_one_domain(tmp_path, missing):
    source = SnapshotPart("source", "items", b"parent,child\n1,2\n2,1\n1,1\n")
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64,
        "domains": [{"name": "linked", "mapping": {"kind": "inline", "entries": [
            {"original": [1, 2], "replacement": [11, 12]},
            {"original": [1, 1], "replacement": [11, 11]},
            *([] if missing else [{"original": [2, 1], "replacement": [12, 11]}])]}}],
        "fields": [{"entity": "items", "field": name, "sensitivity": "non_sensitive",
            "behavior": {"action": "substitute", "mapping": {
                "kind": "domain", "name": "linked", "component": component}}}
            for component, name in enumerate(("parent", "child"))]})
    profile = _profile_transformation_source(source, policy,
        max_bytes=8192, budget=GenerationBudget(5))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    source_path, policy_path = tmp_path / "items.csv", tmp_path / "behavior.yaml"
    source_path.write_bytes(source.payload)
    policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    before = (source_path.read_bytes(), policy_path.read_bytes())

    def cli(command, *arguments):
        return subprocess.run([sys.executable, "-m", "test_data_agent.cli", command,
            str(source_path), str(policy_path), *map(str, arguments), "--json"],
            capture_output=True, text=True, timeout=15)

    review = cli("transform-review")
    assert review.returncode == 0, review.stderr
    digest = json.loads(review.stdout)["result"]["snapshot_sha256"]
    output_path = tmp_path / "output"
    result = cli("transform-execute", output_path, "--snapshot-sha256", digest)
    if missing:
        assert result.returncode != 0 and not output_path.exists()
        assert not any(path.name.startswith(".output") for path in tmp_path.iterdir())
    else:
        assert result.returncode == 0, result.stderr
        with (output_path / "dataset.csv").open(newline="") as output:
            rows = list(csv.reader(output))
        assert rows == [["parent", "child"], ["11", "12"], ["12", "11"], ["11", "11"]]
    assert before == (source_path.read_bytes(), policy_path.read_bytes())
