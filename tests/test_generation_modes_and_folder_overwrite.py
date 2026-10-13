"""Executable modes and rollback with fictional data only."""
import json

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io import path_policy
from test_data_agent.io.commands import generate_dataset_from_spec_path
from test_data_agent.io.workflows import generate_dataset_bundle


def boundary_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({"entities": [{"name": "item", "row_count": 6, "fields": [
        {"name": "quantity", "data_type": "integer", "distribution": {"kind": "numeric", "min_value": -2, "max_value": 5}},
        {"name": "price", "data_type": "decimal", "distribution": {"kind": "decimal_range", "min": "-1.20", "max": "3.40", "precision": 4, "scale": 2}},
        {"name": "day", "data_type": "date", "distribution": {"kind": "date_range", "min": "2023-01-01", "max": "2023-12-31"}},
        {"name": "label", "data_type": "string", "distribution": {"kind": "string_pattern", "min_length": 2, "max_length": 9}},
        {"name": "active", "data_type": "boolean"},
        {"name": "optional", "data_type": "integer", "nullable": True, "null_ratio": .1},
    ]}]})


def test_edge_covers_boundaries_without_invalid_rows(tmp_path):
    spec = boundary_spec()
    spec.generation_settings.mode = GenerationMode.EDGE
    rows = generate_dataset(spec, seed=13)["item"]
    assert rows == generate_dataset(spec, seed=13)["item"]
    assert {row["quantity"] for row in rows} == {-2, 0, 5}
    assert {str(row["price"]) for row in rows} == {"-1.20", "0.00", "3.40"}
    assert {row["day"] for row in rows} == {"2023-01-01", "2023-12-31"}
    assert {len(row["label"]) for row in rows} == {2, 9}
    assert {row["active"] for row in rows} == {True, False}
    assert any(row["optional"] is None for row in rows)
    assert generate_dataset_bundle(spec, output_folder=tmp_path / "edge").validation.valid


def test_load_volume_is_expanded_once_and_count_overrides(tmp_path):
    spec = boundary_spec()
    spec.generation_settings.mode = GenerationMode.LOAD_TEST
    assert len(generate_dataset(spec, seed=13)["item"]) == 60
    assert spec.entities[0].row_count == 6
    result = generate_dataset_bundle(spec, output_folder=tmp_path / "load")
    assert result.row_counts == {"item": 60}
    assert json.loads((tmp_path / "load" / "generation_manifest.json").read_text())["row_counts"] == {"item": 60}
    result = generate_dataset_bundle(spec, output_folder=tmp_path / "exact", count=7)
    assert result.row_counts == {"item": 7}


def test_overwrite_restores_old_directory_on_publication_failure(tmp_path, monkeypatch):
    old = tmp_path / "out"
    old.mkdir()
    (old / "keep.txt").write_text("fictional previous output")
    staged = path_policy.make_staging_directory(old)
    (staged / "new.txt").write_text("fictional replacement")
    real_replace = path_policy.os.replace
    def fail_new(source, destination, **kwargs):
        if source == staged.name:
            raise OSError("fictional publication failure")
        return real_replace(source, destination, **kwargs)
    monkeypatch.setattr(path_policy.os, "replace", fail_new)
    with pytest.raises(ValueError, match="unsafe filesystem path"):
        path_policy.publish_directory(staged, old, overwrite=True)
    assert (old / "keep.txt").read_text() == "fictional previous output"
    assert list(old.iterdir()) == [old / "keep.txt"]


def test_overwrite_rejects_symlink_and_input_inside_output(tmp_path):
    old = tmp_path / "old"
    old.mkdir()
    (old / "keep").write_text("fictional")
    link = tmp_path / "link"
    link.symlink_to(old, target_is_directory=True)
    with pytest.raises(ValueError, match="folder"):
        generate_dataset_bundle(boundary_spec(), output_folder=link, overwrite=True)
    spec = old / "spec.json"
    spec.write_text(boundary_spec().model_dump_json())
    with pytest.raises(ValueError, match="contain the input"):
        generate_dataset_from_spec_path(spec, output_folder=old, overwrite=True)
    assert (old / "keep").read_text() == "fictional"


def test_overwrite_restores_old_output_after_fsync_failure(tmp_path, monkeypatch):
    old = tmp_path / "out"
    old.mkdir()
    (old / "keep").write_text("fictional")
    staged = path_policy.make_staging_directory(old)
    (staged / "new").write_text("fictional")
    def fail_sync(descriptor):
        raise OSError("fictional disk failure")
    monkeypatch.setattr(path_policy.os, "fsync", fail_sync)
    with pytest.raises(ValueError, match="unsafe filesystem path"):
        path_policy.publish_directory(staged, old, overwrite=True)
    assert [p.name for p in old.iterdir()] == ["keep"]
    assert (old / "keep").read_text() == "fictional"


def test_load_budget_rejects_expansion_before_rows_or_publication(tmp_path, monkeypatch):
    from test_data_agent.core.limits import GenerationLimitError
    spec = boundary_spec()
    spec.generation_settings.mode = GenerationMode.LOAD_TEST
    spec.generation_settings.load_multiplier = 10**12
    with pytest.raises((ValueError, GenerationLimitError)):
        generate_dataset_bundle(spec, output_folder=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_failed_generation_preserves_old_folder(tmp_path, monkeypatch):
    from test_data_agent.io import workflows
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("fictional")
    def fail_generation(*args, **kwargs):
        raise ValueError("fictional constraint failure")
    monkeypatch.setattr(workflows, "generate_dataset", fail_generation)
    with pytest.raises(ValueError, match="constraint failure"):
        generate_dataset_bundle(boundary_spec(), output_folder=out, overwrite=True)
    assert [p.name for p in out.iterdir()] == ["keep"]


def test_cleanup_failure_keeps_published_replacement(tmp_path, monkeypatch):
    old = tmp_path / "out"
    old.mkdir()
    (old / "keep").write_text("fictional")
    staged = path_policy.make_staging_directory(old)
    (staged / "new").write_text("fictional")
    real_remove = path_policy.shutil.rmtree
    def fail_backup(path, **kwargs):
        if str(path).endswith(".rollback"):
            raise OSError("fictional cleanup failure")
        return real_remove(path, **kwargs)
    fail_backup.avoids_symlink_attacks = True
    monkeypatch.setattr(path_policy.shutil, "rmtree", fail_backup)
    path_policy.publish_directory(staged, old, overwrite=True)
    assert (old / "new").read_text() == "fictional"
    assert len(list(tmp_path.glob(".*.rollback"))) == 1


def test_interruption_immediately_after_rename_restores_previous_folder(tmp_path, monkeypatch):
    old = tmp_path / "out"
    old.mkdir()
    (old / "keep").write_text("fictional")
    staged = path_policy.make_staging_directory(old)
    (staged / "new").write_text("fictional")
    real_replace = path_policy.os.replace
    def interrupt_after_replace(*args, **kwargs):
        real_replace(*args, **kwargs)
        raise KeyboardInterrupt
    monkeypatch.setattr(path_policy.os, "replace", interrupt_after_replace)
    with pytest.raises(KeyboardInterrupt):
        path_policy.publish_directory(staged, old, overwrite=True)
    assert [p.name for p in old.iterdir()] == ["keep"]


def test_agent_plan_preserves_explicit_requested_load_count(tmp_path):
    from test_data_agent.agent_contracts import AgentRequest, AgentSourceType
    from test_data_agent.agent_planning import prepare_spec_for_approval
    spec = boundary_spec()
    request = AgentRequest(source_type=AgentSourceType.CSV, source_path=tmp_path / "fictional.csv",
                           workspace=tmp_path / "work", count=6, mode=GenerationMode.LOAD_TEST)
    prepare_spec_for_approval(spec, request)
    assert len(generate_dataset(spec, seed=request.seed)["item"]) == 6


def test_cli_load_count_is_exact(tmp_path):
    from test_data_agent.cli import main
    spec = tmp_path / "spec.json"
    spec.write_text(boundary_spec().model_dump_json())
    output = tmp_path / "out"
    assert main(["generate", str(spec), "--mode", "load_test", "--count", "7", "--output", str(output)]) == 0
    assert json.loads((output / "generation_manifest.json").read_text())["row_counts"] == {"item": 7}


def test_custom_load_multiplier_and_profile_count(tmp_path):
    from test_data_agent.core.dataset import DatasetProfile
    from test_data_agent.io.workflows import build_dataset_spec_from_profile
    spec = boundary_spec()
    spec.generation_settings.mode = GenerationMode.LOAD_TEST
    spec.generation_settings.load_multiplier = 3
    assert len(generate_dataset(spec, seed=5)["item"]) == 18
    profile = DatasetProfile.model_validate({"source_type": "csv", "entities": [{"name": "item", "row_count": 2,
        "fields": [{"name": "quantity", "data_type": "integer"}]}]})
    prepared = build_dataset_spec_from_profile(profile, count=7, seed=5, mode="load_test")
    assert len(generate_dataset(prepared, seed=5)["item"]) == 7


@pytest.mark.parametrize("data_type", ["integer", "float"])
def test_edge_respects_numeric_scale_factor(data_type):
    spec = DatasetSpec.model_validate({"generation_settings": {"mode": "edge"},
        "entities": [{"name": "item", "row_count": 2, "fields": [{"name": "amount",
            "data_type": data_type, "distribution": {"kind": "numeric", "min_value": 10,
            "max_value": 20, "scale_factor": 2}}]}]})
    assert {row["amount"] for row in generate_dataset(spec, seed=1)["item"]} == {20, 40}
