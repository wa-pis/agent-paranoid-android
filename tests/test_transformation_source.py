"""Fixed fictional CSV snapshots; no source-preserving execution."""

import os

import pytest

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.csv_profiler import profile_csv, profile_csv_bytes
from test_data_agent.io.transformation_source import (
    TransformationSourceError, load_csv_source_snapshot, revalidate_csv_evidence,
)


def test_fixed_bytes_reprofile_without_reopening_path(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status,amount\nfictional-a,7\nfictional-b,8\n")
    budget = GenerationBudget(5)
    source = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    profile = csv_profile_to_dataset_profile(profile_csv(path, table_name="items"))
    evidence = profile.model_dump_json().encode()
    assert revalidate_csv_evidence(source, evidence, budget=budget, max_bytes=1024) == profile
    path.write_bytes(b"status,amount\nprivate@example.test,7\n")
    assert revalidate_csv_evidence(source, evidence, budget=budget, max_bytes=1024) == profile
    changed = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    with pytest.raises(TransformationSourceError, match="^invalid transformation source evidence$"):
        revalidate_csv_evidence(changed, evidence, budget=budget, max_bytes=1024)


def test_snapshot_matches_existing_profiler_and_rejects_changed_evidence(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status,amount\nfictional-a,0\n,1\n")
    budget = GenerationBudget(5)
    source = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    assert profile_csv_bytes(source.payload, "items", budget=budget, max_bytes=1024) == profile_csv(
        path, table_name="items"
    )
    evidence = csv_profile_to_dataset_profile(profile_csv(path, table_name="items"))
    evidence.entities[0].fields[0].sensitive = True
    with pytest.raises(TransformationSourceError):
        revalidate_csv_evidence(source, evidence.model_dump_json().encode(), budget=budget, max_bytes=1024)


def test_source_loader_rejects_oversize_and_symlink_without_values(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status\nfictional-a\n")
    link = tmp_path / "link.csv"
    link.symlink_to(path)
    for candidate, max_bytes in ((path, 4), (link, 1024)):
        with pytest.raises(TransformationSourceError, match="^invalid transformation source$") as error:
            load_csv_source_snapshot(candidate, "items", budget=GenerationBudget(5), max_bytes=max_bytes)
        assert "fictional-a" not in str(error.value)


def test_source_loader_rejects_fifo_without_blocking(tmp_path):
    path = tmp_path / "source.pipe"
    os.mkfifo(path)
    with pytest.raises(TransformationSourceError):
        load_csv_source_snapshot(path, "items", budget=GenerationBudget(5), max_bytes=1024)
