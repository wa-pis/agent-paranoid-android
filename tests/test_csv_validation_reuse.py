"""Validation fusion preserves public CSV safety and seeded bytes."""

from pathlib import Path

import pytest

from scripts.benchmark_parallel_generation import fictional_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode, OutputFormat, ValidationSettings
from test_data_agent.generation import entity_generator
from test_data_agent.io import workflows
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation import validate_dataset
from test_data_agent.validation.reconciliation import GenerationValidationError


def test_csv_report_and_bytes_match_public_generator_and_standalone_validation(tmp_path: Path) -> None:
    spec = fictional_spec(9)
    spec.generation_settings.seed = 42
    spec.generation_settings.output_format = OutputFormat.CSV
    original = spec.model_dump()
    rows = entity_generator.generate_dataset(spec, seed=42)
    expected_report = validate_dataset(rows, spec)

    result = workflows.generate_dataset_bundle(
        spec, output_folder=tmp_path / "out", output_format=OutputFormat.CSV, seed=42,
    )

    assert result.validation == expected_report
    assert (tmp_path / "out/fictional.csv").read_bytes() == rows_to_csv(rows["fictional"], typed=True).encode()
    assert spec.model_dump() == original


def test_disabled_temporal_report_matches_standalone_validation(tmp_path: Path) -> None:
    spec = DatasetSpec.model_validate({
        "entities": [{"name": "events", "row_count": 3, "fields": [
            {"name": name, "data_type": "date"} for name in ("start", "end")
        ]}],
        "constraints": [{"type": "temporal", "entity": "events",
                         "fields": ["start", "end"], "confidence": 1}],
        "generation_settings": {"seed": 42, "output_format": "csv"},
        "validation_settings": {"validate_constraints": False},
    })
    rows = entity_generator.generate_dataset(spec, seed=42)
    expected = validate_dataset(rows, spec)

    result = workflows.generate_dataset_bundle(spec, output_folder=tmp_path / "out")

    assert result.validation == expected
    assert result.validation.utility is not None
    assert result.validation.utility.temporal_checks == "not_run"
    assert result.validation.utility.temporal_metrics == []


@pytest.mark.parametrize("violation", ["privacy", "type", "shape", "null"])
def test_candidate_checks_cannot_be_disabled_or_reach_csv_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, violation: str,
) -> None:
    spec = fictional_spec(2)
    spec.validation_settings = ValidationSettings(
        validate_schema=False, validate_relationships=False,
        validate_constraints=False, validate_privacy=False,
    )
    rows = entity_generator.generate_dataset(spec, seed=42)
    if violation == "privacy":
        rows["fictional"][0]["value_4"] = "fictional-canary@example.invalid"
    elif violation == "type":
        rows["fictional"][0]["row_id"] = "synthetic_wrong_type"
    elif violation == "shape":
        del rows["fictional"][0]["value_4"]
    else:
        rows["fictional"][0]["row_id"] = None
    monkeypatch.setattr(workflows, "_generate_dataset_candidates", lambda *a, **kw: rows)
    monkeypatch.setattr(workflows, "write_dataset_rows", lambda *a, **kw: pytest.fail("unsafe CSV write"))
    output = tmp_path / "out"
    output.mkdir()
    (output / "existing").write_text("synthetic_previous")

    with pytest.raises(GenerationValidationError) as caught:
        workflows.generate_dataset_bundle(spec, output_folder=output, output_format=OutputFormat.CSV, seed=42)

    assert "fictional-canary" not in str(caught.value)
    assert (output / "existing").read_text() == "synthetic_previous"
    assert {path.name for path in tmp_path.iterdir()} == {"out"}


def test_business_callback_keeps_fresh_mandatory_validation_with_disabled_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = fictional_spec(2)
    spec.validation_settings.validate_privacy = False
    monkeypatch.setattr(workflows, "_validate_generated_dataset", lambda *a: pytest.fail("callback reused checks"))
    calls = []

    def mutate(rows, seed, effective_spec):
        calls.append(seed)
        rows["fictional"][0]["value_4"] = "fictional-canary@example.invalid"
        effective_spec.validation_settings.validate_privacy = False

    with pytest.raises(GenerationValidationError, match="privacy validation"):
        workflows.generate_dataset_bundle(
            spec, output_folder=tmp_path / "out", output_format=OutputFormat.CSV,
            seed=42, business_rules_applier=mutate,
        )
    assert calls == [42] and not list(tmp_path.iterdir())


def test_public_generator_still_rejects_bad_candidates_before_return_or_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = fictional_spec(1)
    rows = entity_generator.generate_dataset(spec, seed=42)
    rows["fictional"][0]["row_id"] = None
    monkeypatch.setattr(entity_generator, "_generate_dataset_candidates", lambda *a, **kw: rows)

    with pytest.raises(GenerationValidationError):
        entity_generator.generate_dataset(spec, seed=42)
    with pytest.raises(GenerationValidationError):
        workflows.generate_dataset_bundle(
            spec, output_folder=tmp_path / "out", output_format=OutputFormat.CSV,
            business_rules_applier=lambda *a: pytest.fail("unsafe callback"),
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mode", list(GenerationMode))
@pytest.mark.parametrize("output_format", [OutputFormat.JSON, OutputFormat.CSV])
def test_only_valid_csv_without_callback_uses_combined_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    mode: GenerationMode, output_format: OutputFormat,
) -> None:
    spec = fictional_spec(1)
    spec.generation_settings.mode = mode
    actual = workflows._validate_generated_dataset
    called = []

    def combined(*args, **kwargs):
        called.append(True)
        return actual(*args, **kwargs)

    monkeypatch.setattr(workflows, "_validate_generated_dataset", combined)
    workflows.generate_dataset_bundle(
        spec, output_folder=tmp_path / "out", output_format=output_format, seed=42,
    )

    assert bool(called) == (mode == GenerationMode.VALID and output_format == OutputFormat.CSV)
