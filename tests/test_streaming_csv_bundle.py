"""Public streaming CSV keeps bundle contracts and leaves global solving on legacy."""

from __future__ import annotations

import json

import pytest

from scripts.benchmark_parallel_generation import fictional_spec
from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy
from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import RESERVED_ENTITY_ARTIFACT_BASENAMES
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.limits import GenerationLimitError
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.tiled_generator import TILE_ROWS, generate_tile
from test_data_agent.io import streaming_csv, workflows
from test_data_agent.io.artifacts import validate_generation_bundle


@pytest.fixture(autouse=True)
def serial_tiles(monkeypatch):
    def visit(spec, seed, *, policy, budget, consume):
        for index, entity in enumerate(spec.entities):
            for start in range(0, entity.row_count, TILE_ROWS):
                consume(index, start, generate_tile(spec, index, start, seed, budget=budget))
    monkeypatch.setattr(streaming_csv, "_visit_generated_tiles", visit)


def export(spec, path, **kwargs):
    return workflows.generate_dataset_bundle(
        spec, output_folder=path, output_format=OutputFormat.CSV, seed=42,
        streaming=ParallelGenerationPolicy(workers=1, max_rows=1_000_000, max_cells=25_000_000),
        **kwargs,
    )


def test_streaming_publishes_valid_complete_bundle_without_full_size_estimate(tmp_path, monkeypatch):
    def reject_estimate(*args):
        pytest.fail("streaming must enforce actual bytes instead of the full-dataset estimate")
    monkeypatch.setattr(workflows, "estimate_dataset_output_bytes", reject_estimate)
    spec = fictional_spec(4)
    original = spec.model_dump()
    result = export(spec, tmp_path / "out")
    manifest = json.loads((tmp_path / "out/generation_manifest.json").read_text())

    assert result.validation.valid and result.row_counts == {"fictional": 4}
    assert spec.model_dump() == original
    assert manifest["synthetic"] and manifest["source_rows_copied"] is False
    assert manifest["reproducibility"]["generator_algorithm_version"] == "tiled-v1"
    assert manifest["reproducibility"]["serializer"] == "python-stdlib-csv"
    assert "pyarrow" not in manifest["reproducibility"]["dependencies"]
    assert validate_generation_bundle(tmp_path / "out").validation_valid
    assert {path.name for path in (tmp_path / "out").iterdir()} == {
        "fictional.csv", "dataset_spec.yaml", "generation_manifest.json", "validation_report.json",
    }


@pytest.mark.parametrize("kind", ["relationship", "constraint", "callback", "mode", "multiple"])
def test_global_work_remains_on_legacy_with_actual_manifest_engine(tmp_path, monkeypatch, kind):
    spec = fictional_spec(3)
    called = []
    kwargs = {}
    if kind == "relationship":
        spec.entities[0].fields.append(FieldSpec(name="reference", data_type="integer"))
        spec.relationships = [Relationship(parent_entity="fictional", parent_field="row_id",
                                            child_entity="fictional", child_field="reference", confidence=1)]
    elif kind == "constraint":
        spec.constraints = [Constraint(type="formula", entity="fictional", fields=["value_0"],
                                       expression="value_6 + 1", confidence=1, status="confirmed")]
    elif kind == "callback":
        def callback(data, seed, effective_spec):
            called.append((len(data["fictional"]), seed))
        kwargs["business_rules_applier"] = callback
    elif kind == "mode":
        spec.generation_settings.mode = "edge"
    else:
        other = spec.entities[0].model_copy(deep=True)
        other.name = "other"
        spec.entities.append(other)
    monkeypatch.setattr(workflows, "write_streaming_csv", lambda *a, **kw: pytest.fail("fallback streamed"))

    export(spec, tmp_path / "out", **kwargs)

    manifest = json.loads((tmp_path / "out/generation_manifest.json").read_text())
    assert manifest["reproducibility"]["generator_algorithm_version"] == manifest["package_version"]
    if kind == "callback":
        assert called == [(3, 42)]


def test_large_override_does_not_raise_legacy_fallback_limits(tmp_path):
    spec = fictional_spec(100_001)
    with pytest.raises(ValueError, match="100000"):
        export(spec, tmp_path / "out", business_rules_applier=lambda *args: None)
    assert not list(tmp_path.iterdir())


def test_actual_complete_bundle_byte_budget_is_preserved(tmp_path, monkeypatch):
    export(fictional_spec(2), tmp_path / "baseline")
    total = sum(path.stat().st_size for path in (tmp_path / "baseline").iterdir())
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", str(total - 1))

    with pytest.raises(GenerationLimitError):
        export(fictional_spec(2), tmp_path / "out")

    assert not (tmp_path / "out").exists()
    assert {path.name for path in tmp_path.iterdir()} == {"baseline"}


@pytest.mark.parametrize("stage", ["write_dataset_spec_artifact", "write_dataset_validation_report",
                                   "write_generation_manifest", "commit_temp_output_folder"])
def test_failure_after_streaming_never_publishes_partial_bundle(tmp_path, monkeypatch, stage):
    def fail(*args, **kwargs):
        raise OSError("synthetic publication failure")
    monkeypatch.setattr(workflows, stage, fail)

    with pytest.raises(OSError):
        export(fictional_spec(2), tmp_path / "out")

    assert not list(tmp_path.iterdir())


def test_streaming_never_replaces_existing_bundle(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    existing = output / "synthetic_existing.txt"
    existing.write_text("synthetic_previous_output")

    with pytest.raises(ValueError):
        export(fictional_spec(2), output)

    assert existing.read_text() == "synthetic_previous_output"
    assert {path.name for path in tmp_path.iterdir()} == {"out"}


def test_python_streaming_rejects_non_csv_before_output(tmp_path):
    with pytest.raises(ValueError, match="CSV"):
        workflows.generate_dataset_bundle(fictional_spec(2), output_folder=tmp_path / "out",
                                          streaming=ParallelGenerationPolicy())
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name", sorted(RESERVED_ENTITY_ARTIFACT_BASENAMES))
def test_mutated_reserved_entity_name_is_rejected_before_workers(tmp_path, monkeypatch, name):
    spec = fictional_spec(2)
    spec.entities[0].name = name
    monkeypatch.setattr(streaming_csv, "_visit_generated_tiles",
                        lambda *args, **kwargs: pytest.fail("reserved name reached worker startup"))

    with pytest.raises(streaming_csv.StreamingCsvError, match="streaming CSV"):
        export(spec, tmp_path / "out")

    assert not list(tmp_path.iterdir())


def test_mutated_duplicate_spec_fields_are_revalidated_before_workers(tmp_path, monkeypatch):
    spec = fictional_spec(2)
    spec.entities[0].fields.append(spec.entities[0].fields[0].model_copy(deep=True))
    monkeypatch.setattr(streaming_csv, "_visit_generated_tiles",
                        lambda *args, **kwargs: pytest.fail("invalid specification reached workers"))

    with pytest.raises(streaming_csv.StreamingCsvError):
        export(spec, tmp_path / "out")

    assert not list(tmp_path.iterdir())
