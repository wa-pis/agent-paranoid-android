"""Installed literal replacement versus explicit DATETIME output conversion."""

import csv
import io
import json
import subprocess
import sys
from datetime import datetime, timezone

import pytest
import yaml
import pyarrow.parquet as pq

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source


@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_literal_mapping_then_explicit_temporal_output(tmp_path, output_format):
    source = SnapshotPart("source", "items", b"label,instant\nindigo,2026-08-31 03:15:00\n")
    data = {"schema_version": "0.1", "seed": 72, "schema_fingerprint": "0" * 64,
        "fields": [
            {"entity": "items", "field": "label", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": ["indigo"], "replacement": ["olive"]}]}}},
            {"entity": "items", "field": "instant", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv", "path": "times.csv",
                 "source_columns": ["old"], "replacement_columns": ["new"]}}}]}
    if output_format != "csv":
        data["output"] = {"format": output_format, "fields": [
            {"name": "label", "type": "string"},
            {"name": "instant", "type": "datetime", "temporal_type": {
                "type": "datetime", "format": "%Y-%m-%d %H:%M:%S",
                "output_format": "%Y-%m-%dT%H:%M:%S.%f%z",
                "source_timezone": "Europe/Samara", "target_timezone": "UTC"}}]}
        if output_format == "postgresql_sql":
            data["output"]["table"] = "items"
    policy = BehaviorPolicy.model_validate(data)
    profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
    data["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    source_path, policy_path = tmp_path / "items.csv", tmp_path / "behavior.yaml"
    source_path.write_bytes(source.payload)
    policy_path.write_text(yaml.safe_dump(data))
    mapping = tmp_path / "times.csv"
    mapping.write_bytes(b"old,new\n2026-08-31 03:15:00,2027-03-04 04:05:00\n")
    before = source_path.read_bytes(), policy_path.read_bytes(), mapping.read_bytes()
    def cli(*arguments):
        return subprocess.run([sys.executable, "-m", "test_data_agent.cli", *map(str, arguments)],
            capture_output=True, text=True, timeout=30, check=False)
    review = cli("transform-review", source_path, policy_path)
    assert review.returncode == 0
    destination = tmp_path / "output"
    execution = cli("transform-execute", source_path, policy_path, destination,
        "--snapshot-sha256", json.loads(review.stdout)["snapshot_sha256"], "--json")
    assert execution.returncode == 0
    assert all(value not in review.stdout + execution.stdout for value in (
        "indigo", "olive", "2026-08-31", "2027-03-04"))
    if output_format == "csv":
        assert list(csv.reader(io.StringIO((destination / "dataset.csv").read_text()))) == [
            ["label", "instant"], ["olive", "2027-03-04 04:05:00"]]
    elif output_format == "parquet":
        assert pq.read_table(destination / "dataset.parquet").to_pylist() == [{
            "label": "olive", "instant": datetime(2027, 3, 4, 0, 5, tzinfo=timezone.utc)}]
    else:
        sql = (destination / "dataset.sql").read_text()
        assert "TIMESTAMPTZ '2027-03-04 00:05:00+00:00'" in sql
        assert "2027-03-04 04:05:00" not in sql
    assert before == (source_path.read_bytes(), policy_path.read_bytes(), mapping.read_bytes())
