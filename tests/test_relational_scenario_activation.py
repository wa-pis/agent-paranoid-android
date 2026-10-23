"""Fictional end-to-end candidate evidence for reviewed relationship scenarios."""
import json
from copy import deepcopy

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.settings import OutputFormat, ValidationSettings
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.io.writers import write_dataset_rows
from test_data_agent.postgres_sql_export import render_postgres_sql
from test_data_agent.validation.reconciliation import GenerationValidationError, assert_generated_dataset_valid, validate_dataset
from tests.test_relational_scenario_preflight import scenario, spec


def configured(*, orphans=0, one_to_one=False):
    source = spec(mode="mixed" if orphans else "valid", one_to_one=one_to_one)
    source.relational_scenarios = [scenario(orphan_count=orphans, fanout_counts=(1, 1, 1) if one_to_one else (3, 3 - orphans, 0))]
    return source


def test_omitted_option_preserves_prior_payload_identity_and_assignments():
    source = spec()
    before = source.model_dump()
    assert "relational_scenarios" not in before
    explicit = DatasetSpec.model_validate({**before, "relational_scenarios": []})
    assert source.model_dump_json() == explicit.model_dump_json()
    assert model_fingerprint(source) == model_fingerprint(explicit)
    assert generate_dataset(source, seed=7) == generate_dataset(explicit, seed=7)
    assert "relational_scenarios" not in validate_dataset(generate_dataset(source, seed=7), source).model_dump()


@pytest.mark.parametrize("orphans", [0, 2])
def test_generated_scenarios_bind_evidence_and_keep_expected_invalid_status(orphans):
    source = configured(orphans=orphans)
    data = generate_dataset(source, seed=7)
    assert data == generate_dataset(source, seed=7)
    report = validate_dataset(data, source)
    assert report.relational_scenarios.expectations_met
    assert report.relational_scenarios.spec_sha256 == model_fingerprint(source)
    assert report.relational_scenarios.observations[0].observed_orphan_count == orphans
    assert report.valid == (orphans == 0)
    assert_generated_dataset_valid(data, source)


def test_generation_skips_unsplit_one_to_one_capacity_rejection():
    source = configured(orphans=3, one_to_one=True)
    data = generate_dataset(source, seed=-7)
    assert len({row["parent_key"] for row in data["children"]}) == 6
    assert validate_dataset(data, source).relational_scenarios.expectations_met


def test_disabled_reports_cannot_hide_expected_invalids_or_bypass_reconciliation(tmp_path):
    source = configured(orphans=2)
    source.validation_settings = ValidationSettings(validate_schema=False, validate_relationships=False,
        validate_constraints=False, validate_privacy=False)
    data = generate_dataset(source, seed=7)
    report = validate_dataset(data, source)
    assert not report.valid and report.relational_scenarios.expectations_met
    data["children"][0]["parent_key"] = -1000
    assert not validate_dataset(data, source).relational_scenarios.expectations_met
    output = tmp_path / "out"
    with pytest.raises(GenerationValidationError):
        write_dataset_rows(data, OutputFormat.JSON, output, spec=source)
    assert not output.exists()


@pytest.mark.parametrize("output_format", [OutputFormat.JSON, OutputFormat.CSV, OutputFormat.PARQUET])
def test_bundle_publishes_controlled_invalid_report_without_claiming_validity(tmp_path, output_format):
    source = configured(orphans=2)
    output = tmp_path / "out"
    generate_dataset_bundle(source, output_folder=output, output_format=output_format, seed=7)
    report = json.loads((output / "validation_report.json").read_text())
    assert not report["valid"] and report["relational_scenarios"]["expectations_met"]
    assert report["relational_scenarios"]["observations"][0]["observed_fanout_counts"] == [3, 1, 0]
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert not manifest["validation_valid"]


def test_count_override_invalidates_allocation_before_output(tmp_path):
    source = configured()
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("fictional prior output")
    with pytest.raises(ValueError, match="fan-out"):
        generate_dataset_bundle(source, output_folder=output, count=4, overwrite=True)
    assert sentinel.read_text() == "fictional prior output"
    assert list(output.iterdir()) == [sentinel]


def test_controlled_orphans_cannot_be_exported_with_sql_foreign_key_ddl():
    source = configured(orphans=2)
    data = generate_dataset(source, seed=7)
    with pytest.raises(ValueError):
        render_postgres_sql(source, data)


def test_post_generation_non_key_type_failure_is_mandatory_with_disabled_reports(tmp_path):
    source = configured(orphans=2)
    source.validation_settings = ValidationSettings(validate_schema=False, validate_relationships=False,
        validate_constraints=False, validate_privacy=False)
    source.entities[1].fields.append(source.entities[1].fields[0].model_copy(update={"name": "quantity", "is_identifier": False}))
    data = generate_dataset(source, seed=7)
    data["children"][0]["quantity"] = "invalid-number"
    before = deepcopy(data)
    assert not validate_dataset(data, source).valid
    with pytest.raises(GenerationValidationError, match="type"):
        write_dataset_rows(data, OutputFormat.JSON, tmp_path / "out", spec=source)
    assert data == before and not (tmp_path / "out").exists()


def test_review_warning_discloses_requested_invalid_count_without_generated_keys():
    from test_data_agent.agent_planning import plan_warnings
    warnings = " ".join(plan_warnings(configured(orphans=2)))
    assert "2 synthetic missing-parent references" in warnings
    assert "parent ordinal" in warnings


def test_report_observation_marks_one_to_one_duplicates_unexpected():
    source = configured(orphans=3, one_to_one=True)
    source.relational_scenarios = [scenario(orphan_count=3)]
    data = generate_dataset(source, seed=7)
    valid_children = [row for row in data["children"] if row["parent_key"] > 0]
    valid_children[1]["parent_key"] = valid_children[0]["parent_key"]
    evidence = validate_dataset(data, source).relational_scenarios
    assert not evidence.expectations_met
    assert not evidence.observations[0].valid
    assert not evidence.observations[0].expectations_met


@pytest.mark.parametrize("orphans,exit_code", [(0, 0), (2, 1)])
def test_cli_generates_saved_reviewed_scenario_with_expected_exit_status(tmp_path, orphans, exit_code):
    from test_data_agent.cli import main
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(configured(orphans=orphans).model_dump_json())
    output = tmp_path / "out"
    assert main(["generate", str(spec_path), "--output", str(output), "--seed", "7"]) == exit_code
    report = json.loads((output / "validation_report.json").read_text())
    assert report["relational_scenarios"]["expectations_met"]
    assert report["valid"] == (orphans == 0)


def test_mcp_consumes_reviewed_spec_without_returning_generated_keys(tmp_path, monkeypatch):
    from test_data_agent.mcp_generator_server import generate_dataset as mcp_generate
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "spec.json").write_text(configured(orphans=2).model_dump_json())
    result = mcp_generate("spec.json", "out", seed=7)
    assert "rows" not in result
    assert "14000001" not in json.dumps(result)
    report = json.loads((tmp_path / "out/validation_report.json").read_text())
    assert report["relational_scenarios"]["expectations_met"] and not report["valid"]


@pytest.mark.parametrize("kind", ["float", "boolean", "decimal"])
def test_explicit_scenario_keeps_unrelated_native_key_types_supported(kind):
    source = configured()
    payload = source.model_dump(mode="json")
    field = {"name": "value", "data_type": kind}
    if kind == "decimal":
        field["distribution"] = {"kind": "decimal_range", "min": "-1.00", "max": "1.00", "precision": 4, "scale": 2}
    payload["entities"].extend([
        {"name": "metric_parents", "row_count": 3, "fields": [field]},
        {"name": "metric_children", "row_count": 6, "fields": [field]},
    ])
    payload["relationships"].append({"parent_entity": "metric_parents", "parent_field": "value",
        "child_entity": "metric_children", "child_field": "value", "confidence": 1})
    source = DatasetSpec.model_validate(payload)
    baseline = source.model_copy(deep=True)
    baseline.relational_scenarios = []
    ordinary = generate_dataset(baseline, seed=7)
    actual = generate_dataset(source, seed=7)
    assert actual["metric_parents"] == ordinary["metric_parents"]
    assert actual["metric_children"] == ordinary["metric_children"]
    assert validate_dataset(actual, source).valid
