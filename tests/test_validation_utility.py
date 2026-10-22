"""Utility evidence describes generated checks, never unobserved source fidelity."""
import json

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.constraint import ConstraintStatus
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.io.artifacts import dataset_spec_fingerprint
from test_data_agent.validation import DatasetValidationReport, validate_dataset


def utility_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "parent", "row_count": 2, "fields": [
                {"name": "key", "data_type": "integer", "is_identifier": True}]},
            {"name": "child", "row_count": 7, "fields": [
                {"name": "parent_key", "data_type": "integer", "nullable": True},
                {"name": "start", "data_type": "date"},
                {"name": "end", "data_type": "date"}]}],
        "relationships": [{"parent_entity": "parent", "parent_field": "key",
                           "child_entity": "child", "child_field": "parent_key", "confidence": 1}],
        "constraints": [{"type": "temporal", "entity": "child", "fields": ["start", "end"],
                         "confidence": 1}],
    })


def test_no_declarations_are_untested_and_legacy_reports_still_parse():
    spec = DatasetSpec()
    report = validate_dataset({}, spec)
    assert report.valid
    assert report.utility.relationship_checks == "not_declared"
    assert report.utility.temporal_checks == "not_declared"
    assert report.utility.active_relationships == 0
    assert report.utility.unmodeled_relationship_count is None
    assert report.utility.source_orphan_ratio is None
    assert report.utility.source_fanout is None
    assert report.utility.source_temporal_fidelity == "unmeasured"
    assert report.utility.spec_sha256 == dataset_spec_fingerprint(spec)
    legacy = DatasetValidationReport(valid=True, sections=[])
    assert "utility" not in legacy.model_dump(mode="json")


@pytest.mark.parametrize("disabled", [True, False])
def test_disabled_and_fail_fast_checks_are_not_reported_as_executed(disabled):
    spec = utility_spec()
    if disabled:
        spec.validation_settings.validate_relationships = False
        spec.validation_settings.validate_constraints = False
    else:
        spec.validation_settings.fail_fast = True
    report = validate_dataset({"parent": [{"key": "wrong-type"}], "child": []}, spec)
    assert report.utility.relationship_checks == "not_run"
    assert report.utility.temporal_checks == "not_run"
    assert report.utility.active_relationships == report.utility.active_temporal_constraints == 1
    assert report.utility.temporal_metrics == []


def test_measured_zero_differs_from_no_references_and_source_unknowns():
    spec = utility_spec()
    spec.constraints = []
    rows = {"parent": [], "child": [{"parent_key": 19, "start": "2020-01-01", "end": "2020-01-02"}]}
    report = validate_dataset(rows, spec)
    metric = next(s for s in report.sections if s.name == "relationships").relationship_metrics[0]
    assert metric.parent_distinct_keys == metric.resolved_references == 0
    assert metric.checked_references == 1
    assert metric.resolution_ratio == 0
    assert report.utility.source_orphan_ratio is None
    rows["child"] = []
    report = validate_dataset(rows, spec)
    metric = next(s for s in report.sections if s.name == "relationships").relationship_metrics[0]
    assert metric.checked_references == 0
    assert metric.resolution_ratio is None
    assert report.utility.relationship_checks == "executed"


def test_temporal_metrics_count_real_checks_and_exclude_values():
    spec = utility_spec()
    rows = {"parent": [{"key": 1}], "child": [
        {"parent_key": 1, "start": "2020-01-01", "end": "2020-01-02"},
        {"parent_key": None, "start": "2020-01-03", "end": "2020-01-02"},
        {"parent_key": None, "start": None, "end": None}]}
    report = validate_dataset(rows, spec)
    metric = report.utility.temporal_metrics[0]
    assert (metric.checked_rows, metric.failed_rows) == (3, 2)
    assert report.utility.temporal_checks == "executed"
    payload = report.utility.model_dump_json()
    assert "2020" not in payload
    assert report.utility.source_temporal_fidelity == "unmeasured"
    report = validate_dataset({"parent": [], "child": []}, spec)
    metric = report.utility.temporal_metrics[0]
    assert (metric.checked_rows, metric.failed_rows) == (0, 0)
    assert report.utility.source_temporal_fidelity == "unmeasured"


def test_rejected_declarations_do_not_count_as_active_checks():
    spec = utility_spec()
    spec.relationships[0].status = "rejected"
    spec.constraints[0].status = ConstraintStatus.REJECTED
    evidence = validate_dataset({"parent": [], "child": []}, spec).utility
    assert evidence.active_relationships == evidence.active_temporal_constraints == 0
    assert evidence.relationship_checks == evidence.temporal_checks == "not_declared"
    assert evidence.temporal_metrics == []


def test_utility_is_hash_bound_and_cli_replay_is_deterministic(tmp_path):
    spec = utility_spec()
    path = tmp_path / "spec.json"
    path.write_text(spec.model_dump_json())
    reports = []
    for name in ("first", "second"):
        out = tmp_path / name
        assert main(["generate", str(path), "--output", str(out), "--format", "json", "--seed", "13"]) == 0
        report = json.loads((out / "validation_report.json").read_text())
        manifest = json.loads((out / "generation_manifest.json").read_text())
        assert report["utility"]["spec_sha256"] == manifest["spec_sha256"]
        assert report["utility"]["temporal_metrics"][0]["checked_rows"] == 7
        reports.append(report)
    assert reports[0] == reports[1]
    spec.entities[1].row_count = 8
    assert dataset_spec_fingerprint(spec) != reports[0]["utility"]["spec_sha256"]


def test_utility_obeys_existing_deadline():
    ticks = iter([0, 2])
    budget = GenerationBudget(max_seconds=1, clock=lambda: next(ticks))
    with pytest.raises(GenerationLimitError):
        validate_dataset({}, DatasetSpec(), budget=budget)
