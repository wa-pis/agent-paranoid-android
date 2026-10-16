"""Fictional high-risk option interactions, beyond the route matrix."""

from decimal import Decimal
import json

import pytest
import yaml

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat, ValidationSettings
from test_data_agent.generation import generate_dataset
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.validation import validate_dataset


def _decimal_rules_spec():
    def field(name, low, high):
        return {"name": name, "data_type": "decimal", "semantic_type": "numeric_measure",
                "distribution": {"kind": "decimal_range", "precision": 38, "scale": 16,
                                 "min": low, "max": high}}
    return DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 3,
        "fields": [field("base_amount", "9007199254740993.125", "9007199254740993.125"),
                   field("total", "0", "99999999999999999")]}],
        "business_rules": {"row_rules": [{"type": "formula", "table": "items",
            "field": "total", "expression": "base_amount * 0.5"}],
            "cross_table_rules": [{"type": "aggregate_formula", "table": "items",
                "field": "total", "expression": "sum('base_amount') * 0.5"}]}})


def _run_interface(spec, interface, output_format, root, monkeypatch, count=None):
    controlled_invalid = spec.generation_settings.mode in {"negative", "mixed"}
    source = root / "spec.json"
    source.write_text(spec.model_dump_json())
    output = root / "output"
    if interface == "bundle":
        generate_dataset_bundle(spec, output_folder=output, output_format=output_format,
                                seed=7, count=count)
    elif interface == "cli":
        from test_data_agent.cli import main
        arguments = ["generate", str(source), "--output", str(output), "--format",
                     output_format.value, "--seed", "7"]
        if count is not None:
            arguments.extend(["--count", str(count)])
        assert main(arguments) == int(controlled_invalid)
    elif interface == "mcp":
        import test_data_agent.mcp_generator_server as server
        monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(root))
        result = server.generate_dataset("spec.json", "output", output_format=output_format.value,
                                         seed=7, count=count)
        assert result["validation"]["valid"] is not controlled_invalid
    else:
        from test_data_agent.agent import (
            approve_agent_workspace, inspect_agent_workspace, plan_agent_request,
        )
        from test_data_agent.agent_contracts import AgentRequest
        input_path = root / "fictional.csv"
        input_path.write_text("base_amount,total\n2,0\n3,1\n")
        workspace = root / "agent"
        plan_agent_request(AgentRequest(source_type="csv", source_path=input_path,
            workspace=workspace, table_name="items", count=3, seed=7,
            output_format=output_format))
        spec.generation_settings.seed = 7
        spec.generation_settings.output_format = output_format
        (workspace / "dataset_spec.yaml").write_text(yaml.safe_dump(spec.model_dump(mode="json")))
        reviewed = inspect_agent_workspace(workspace)
        approve_agent_workspace(workspace, reviewed_spec_sha256=reviewed.review.current_spec_sha256)
        output = workspace / "generated"
    return output


@pytest.mark.parametrize("interface", ["bundle", "cli", "mcp", "reviewed_agent"])
@pytest.mark.parametrize("output_format", list(OutputFormat))
def test_exact_decimal_formula_aggregate_and_interface_roundtrip(
    tmp_path, monkeypatch, capsys, interface, output_format,
):
    if output_format is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    output = _run_interface(_decimal_rules_spec(), interface, output_format, tmp_path, monkeypatch)
    rows = load_dataset_rows(output)
    saved = load_dataset_spec(output / "dataset_spec.yaml")
    assert validate_dataset(rows, saved).valid
    assert all(Decimal(str(row["total"])) == Decimal("4503599627370496.5625")
               for row in rows["items"])
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["business_validation"]["assigned_row_count"] == 3
    assert manifest["business_validation"]["unexpected_violation_count"] == 0


@pytest.mark.parametrize("interface", ["bundle", "cli", "mcp"])
def test_nullable_boolean_condition_and_empty_text_survive_csv(
    tmp_path, monkeypatch, capsys, interface,
):
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 4,
        "fields": [{"name": "active", "data_type": "boolean", "distribution": {"kind": "boolean", "true_ratio": 1}},
                   {"name": "optional", "data_type": "string", "nullable": True, "null_ratio": 1},
                   {"name": "empty", "data_type": "string", "nullable": True, "distribution": {"kind": "categorical", "categories": [{"value": ""}]}},
                   {"name": "label", "data_type": "string", "distribution": {"kind": "categorical", "categories": [{"value": "ready"}]}}]}],
        "business_rules": {"row_rules": [
            {"type": "conditional_required", "table": "items", "when": {"field": "optional", "equals": None}, "required_fields": ["label"]},
            {"type": "conditional_allowed_values", "table": "items", "field": "label", "when": {"field": "active", "equals": True}, "allowed_values": ["ready"]}]}})
    output = _run_interface(spec, interface, OutputFormat.CSV, tmp_path, monkeypatch)
    rows = load_dataset_rows(output)
    assert all(row["optional"] is None and row["empty"] == "" for row in rows["items"])
    assert validate_dataset(rows, load_dataset_spec(output / "dataset_spec.yaml")).valid


@pytest.mark.parametrize("interface", ["bundle", "cli", "mcp"])
@pytest.mark.parametrize("count", [None, 7])
def test_foreign_key_load_expansion_and_explicit_count(
    tmp_path, monkeypatch, capsys, interface, count,
):
    spec = DatasetSpec.model_validate({"entities": [
        {"name": "parents", "row_count": 2, "primary_key": "pid", "fields": [{"name": "pid", "data_type": "string", "is_identifier": True}]},
        {"name": "children", "row_count": 3, "fields": [{"name": "pid", "data_type": "string", "is_identifier": True}]}],
        "relationships": [{"parent_entity": "parents", "parent_field": "pid", "child_entity": "children", "child_field": "pid", "confidence": 1}],
        "business_rules": {"cross_table_rules": [{"type": "foreign_key", "parent_table": "parents", "parent_field": "pid", "child_table": "children", "child_field": "pid"}]},
        "generation_settings": {"mode": "load_test"}})
    output = _run_interface(spec, interface, OutputFormat.JSON, tmp_path, monkeypatch, count)
    rows = load_dataset_rows(output)
    expected = {"parents": 20, "children": 30} if count is None else {"parents": count, "children": count}
    assert {name: len(values) for name, values in rows.items()} == expected
    assert {row["pid"] for row in rows["children"]} <= {row["pid"] for row in rows["parents"]}
    assert validate_dataset(rows, load_dataset_spec(output / "dataset_spec.yaml")).valid


@pytest.mark.parametrize("mode", ["negative", "mixed"])
def test_overlapping_required_rules_account_for_one_planned_mutation(mode):
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 6,
        "fields": [{"name": "active", "data_type": "boolean", "distribution": {"kind": "boolean", "true_ratio": 1}},
                   {"name": "label", "data_type": "string", "distribution": {"kind": "categorical", "categories": [{"value": "ready"}]}}]}],
        "business_rules": {"field_rules": [{"table": "items", "field": "label", "required": True}],
            "row_rules": [{"type": "conditional_required", "table": "items", "when": {"field": "active", "equals": True}, "required_fields": ["label"]}]},
        "generation_settings": {"mode": mode, "invalid_ratio": 0.5 if mode == "mixed" else 0}})
    reports = []
    rows = generate_dataset(spec, seed=7, business_reports=reports)
    assert len(rows["items"]) == 6
    assert reports[0].expectations_met
    assert reports[0].unexpected_violation_count == 0
    assert not validate_dataset(rows, spec).valid


@pytest.mark.parametrize("mode", ["negative", "mixed"])
def test_decimal_row_formula_and_aggregate_overlap_are_reported_causally(mode):
    spec = _decimal_rules_spec()
    spec.generation_settings.mode = mode
    spec.generation_settings.invalid_ratio = 0.5 if mode == "mixed" else 0
    reports = []
    rows = generate_dataset(spec, seed=7, business_reports=reports)
    assert reports[0].expectations_met
    assert reports[0].unexpected_violation_count == 0
    assert not validate_dataset(rows, spec).valid


@pytest.mark.parametrize("interface", ["bundle", "cli", "mcp"])
@pytest.mark.parametrize("output_format", list(OutputFormat))
@pytest.mark.parametrize("mode", ["negative", "mixed"])
def test_decimal_overlap_survives_publication_and_standalone_revalidation(
    tmp_path, monkeypatch, capsys, interface, output_format, mode,
):
    if output_format is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    spec = _decimal_rules_spec()
    spec.generation_settings.mode = mode
    spec.generation_settings.invalid_ratio = 0.5 if mode == "mixed" else 0
    output = _run_interface(spec, interface, output_format, tmp_path, monkeypatch)
    rows = load_dataset_rows(output)
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["business_validation"]["expectations_met"]
    assert manifest["business_validation"]["unexpected_violation_count"] == 0
    assert not manifest["validation_valid"]
    report = validate_dataset(rows, load_dataset_spec(output / "dataset_spec.yaml"))
    assert not report.valid


def test_planned_mutations_do_not_authorize_preexisting_unrelated_failure():
    from test_data_agent.rules.business_config import apply_and_validate_business_rules
    from test_data_agent.rules.models import BusinessRules
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "label", "required": True}],
        "cross_table_rules": [{"type": "aggregate_formula", "table": "items",
                               "field": "*", "expression": "count()", "expected": 99}],
    })
    rows = {"items": [{"label": "ready"}, {"label": "ready"}]}
    with pytest.raises(ValueError, match="valid business-rule baseline"):
        apply_and_validate_business_rules(rows, rules, seed=7, mode="negative", invalid_ratio=0)
    assert rows == {"items": [{"label": "ready"}, {"label": "ready"}]}


def test_selected_mutation_that_does_nothing_still_reports_missing_expected(monkeypatch):
    from test_data_agent.rules.business_config import apply_and_validate_business_rules
    from test_data_agent.rules.models import BusinessRules
    import test_data_agent.rules.engine as engine
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "label", "required": True}],
    })
    monkeypatch.setattr(engine, "apply_invalid_case", lambda *args, **kwargs: None)
    report = apply_and_validate_business_rules(
        {"items": [{"label": "ready"}, {"label": "ready"}]},
        rules, seed=7, mode="negative", invalid_ratio=0,
    )
    assert not report.expectations_met
    assert report.missing_expected_violation_count == 2


@pytest.mark.parametrize("output_format", list(OutputFormat))
@pytest.mark.parametrize("violation", ["schema", "privacy", "constraint"])
def test_disabled_report_flags_cannot_publish_mandatory_failures(
    tmp_path, output_format, violation,
):
    if output_format is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 2,
        "fields": [{"name": "quantity", "data_type": "integer", "distribution": {"kind": "numeric", "min_value": 2, "max_value": 2}},
                   {"name": "total", "data_type": "integer"}, {"name": "label", "data_type": "string"}]}],
        "constraints": [{"type": "formula", "entity": "items", "fields": ["total"], "expression": "quantity * 2", "confidence": 1}]})
    spec.validation_settings = ValidationSettings(validate_schema=False, validate_relationships=False,
        validate_constraints=False, validate_privacy=False)
    def mutate(rows, seed):
        if violation == "schema":
            rows["items"][0]["quantity"] = "fictional-wrong-type"
        elif violation == "privacy":
            rows["items"][0]["label"] = "fictional-person@example.invalid"
        else:
            rows["items"][0]["total"] = -1
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="validation"):
        generate_dataset_bundle(spec, output_folder=output, output_format=output_format,
                                seed=7, business_rules_applier=mutate)
    assert not output.exists()
