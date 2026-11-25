"""The optional tiled path retains released DECIMAL and typed CSV contracts."""

from decimal import Decimal
import json

import pytest

from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy, generate_dataset_parallel
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import GenerationExecutionPolicy, OutputFormat
from test_data_agent.generation.tiled_generator import generate_tile
from test_data_agent.io import streaming_csv, workflows
from test_data_agent.io.artifacts import validate_generation_bundle
from test_data_agent.io.readers import load_dataset_rows
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.rules.models import BusinessRules
from test_data_agent.validation.reconciliation import normalize_dataset_values


def decimal_spec(count=7):
    return DatasetSpec(schema_version="1.1", entities=[EntitySpec(
        name="fictional", row_count=count, primary_key="id", fields=[
            FieldSpec(name="id", data_type="integer", is_identifier=True),
            FieldSpec(name="amount", data_type="decimal", distribution={
                "kind": "decimal_range", "precision": 8, "scale": 2,
                "min": "1.25", "max": "9.75",
            }),
            FieldSpec(name="empty_text", data_type="string", nullable=True, distribution={
                "kind": "string_pattern", "min_length": 0, "max_length": 0,
            }),
            FieldSpec(name="missing_text", data_type="string", nullable=True, null_ratio=1),
            FieldSpec(name="note", data_type="string"),
        ],
    )], generation_settings={"seed": 42, "output_format": "csv"})


def test_exact_decimal_tiled_rows_are_worker_independent():
    spec = decimal_spec()
    results = [generate_dataset_parallel(
        spec, 42, policy=ParallelGenerationPolicy(workers=workers),
    ) for workers in (1, 2, 4)]
    assert results[0] == results[1] == results[2]
    assert all(isinstance(row["amount"], Decimal) for row in results[0]["fictional"])
    assert all(row["empty_text"] == "" and row["missing_text"] is None
               for row in results[0]["fictional"])


def test_streaming_retains_typed_csv_and_full_spec_evidence(tmp_path, monkeypatch):
    spec = decimal_spec()
    rows = generate_tile(spec, 0, 0, 42, budget=GenerationBudget())
    rows[0]["note"] = r"\synthetic_literal"
    rows[1]["note"] = "=synthetic_formula"

    def visit(spec, seed, *, policy, budget, consume):
        consume(0, 0, rows[:3])
        consume(0, 3, rows[3:])

    monkeypatch.setattr(streaming_csv, "_visit_generated_tiles", visit)
    output = tmp_path / "out"
    result = generate_dataset_bundle(
        spec, output_folder=output, streaming=ParallelGenerationPolicy(),
    )
    assert (output / "fictional.csv").read_bytes() == rows_to_csv(rows, typed=True).encode()
    decoded = [{**row, "amount": str(row["amount"])} for row in rows]
    assert normalize_dataset_values(load_dataset_rows(output), spec) == ({"fictional": decoded}, [])
    assert result.validation.utility is not None
    assert result.validation.utility.spec_sha256 == model_fingerprint(spec)
    manifest = validate_generation_bundle(output)
    assert manifest.validation_valid
    saved = json.loads((output / "generation_manifest.json").read_text())
    assert saved["csv_encoding"] == "backslash-null-v1"
    assert saved["dataset_spec_schema_version"] == "1.1"


def test_embedded_rules_keep_the_released_generator_and_seed(tmp_path, monkeypatch):
    from test_data_agent.generation.entity_generator import generate_dataset

    spec = decimal_spec()
    spec.business_rules = BusinessRules(field_rules=[{
        "table": "fictional", "field": "amount", "required": True,
        "min_value": "1.25", "max_value": "9.75",
    }])
    assert not streaming_csv.can_stream_csv(spec)
    monkeypatch.setattr(workflows, "write_streaming_csv", lambda *a, **kw: pytest.fail("rules were streamed"))
    output = tmp_path / "out"
    expected = generate_dataset(spec, 42)
    result = generate_dataset_bundle(spec, output_folder=output, streaming=ParallelGenerationPolicy())
    assert result.validation.valid
    decoded = {"fictional": [{**row, "amount": str(row["amount"])} for row in expected["fictional"]]}
    assert normalize_dataset_values(load_dataset_rows(output), spec) == (decoded, [])
    saved = json.loads((output / "generation_manifest.json").read_text())
    assert saved["reproducibility"]["generator_algorithm_version"] != "tiled-v1"


def test_released_execution_policy_is_not_reinterpreted_as_tiled(tmp_path):
    spec = decimal_spec()
    spec.generation_settings.execution_policy = GenerationExecutionPolicy(
        engine="scalable-v1", workers=1, max_rows=100,
        max_cells=1000, max_output_bytes=1_000_000, max_seconds=30,
    )
    # A reviewed execution policy and an independent tiled request cannot share seeds.
    with pytest.raises(ValueError, match="either tiled CSV streaming"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "out",
                                output_format=OutputFormat.CSV, streaming=ParallelGenerationPolicy())
    assert not list(tmp_path.iterdir())
