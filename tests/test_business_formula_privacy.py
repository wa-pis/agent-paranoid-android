"""Fictional formula literals retain privacy vetoes before publication."""

from decimal import Decimal
import json

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation import generate_dataset
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.rules.contract import (
    BusinessRuleContractError, validate_business_rules_for_spec,
)
from test_data_agent.rules.models import BusinessRules


def _spec(*, data_type="integer", mode="assign", **field_options):
    field = {
        "name": "quantity",
        "data_type": data_type,
        "distribution": {
            "kind": "numeric", "min_value": 1, "max_value": 9, "scale_factor": 2,
        },
        **field_options,
    }
    return DatasetSpec.model_validate({
        "entities": [{"name": "records", "row_count": 1, "fields": [field]}],
        "business_rules": {"row_rules": [{
            "type": "formula", "table": "records", "field": field["name"],
            "expression": "123456789", "mode": mode,
        }]},
        "validation_settings": {
            "validate_schema": False, "validate_constraints": False,
            "validate_relationships": False, "validate_privacy": False,
        },
    })


@pytest.mark.parametrize("data_type", ["integer", "float"])
@pytest.mark.parametrize("mode", ["assign", "check"])
@pytest.mark.parametrize("field_options", [
    {"name": "phone"}, {"sensitive": True}, {"semantic_type": "phone"},
])
def test_formula_literal_sensitive_target_is_rejected(data_type, mode, field_options):
    spec = _spec(data_type=data_type, mode=mode, **field_options)
    with pytest.raises(BusinessRuleContractError, match="sensitive field values") as error:
        validate_business_rules_for_spec(spec.business_rules, spec)
    assert "123456789" not in str(error.value)


@pytest.mark.parametrize("interface", ["bundle", "cli", "mcp"])
@pytest.mark.parametrize("output_format", list(OutputFormat))
def test_formula_privacy_refusal_never_publishes(
    tmp_path, monkeypatch, capsys, interface, output_format,
):
    spec = _spec(name="phone", sensitive=True)
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    output = tmp_path / "output"
    if interface == "bundle":
        with pytest.raises(BusinessRuleContractError, match="sensitive field values"):
            generate_dataset_bundle(spec, output_folder=output, output_format=output_format)
    elif interface == "cli":
        from test_data_agent.cli import main

        assert main(["generate", str(source), "--output", str(output),
                     "--format", output_format.value]) == 2
        captured = capsys.readouterr()
        assert "123456789" not in captured.out + captured.err
    else:
        import test_data_agent.mcp_generator_server as server

        monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
        with pytest.raises(ValueError, match="sensitive field values") as error:
            server.generate_dataset("spec.json", "output", output_format=output_format.value)
        assert "123456789" not in str(error.value)
    assert not output.exists()


def test_reviewed_decimal_numeric_measure_formula_literal_remains_supported():
    spec = _spec(data_type="decimal", semantic_type="numeric_measure", distribution={
        "kind": "decimal_range", "precision": 12, "scale": 2,
        "min": "0", "max": "9999999999.99",
    })
    assert generate_dataset(spec, seed=17)["records"][0]["quantity"] == Decimal("123456789.00")


@pytest.mark.parametrize("bound", ["min_value", "max_value"])
@pytest.mark.parametrize("data_type", ["integer", "float"])
def test_typed_numeric_bounds_keep_sensitive_target_veto(bound, data_type):
    spec = _spec(data_type=data_type, sensitive=True)
    spec.business_rules = BusinessRules.model_validate({"field_rules": [{
        "table": "records", "field": "quantity", bound: 2,
    }]})
    with pytest.raises(BusinessRuleContractError, match="sensitive field values"):
        validate_business_rules_for_spec(spec.business_rules, spec)


@pytest.mark.parametrize("rules", [
    {"field_rules": [{"table": "records", "field": "amount", "min_value": "123456789"}]},
    {"field_rules": [{"table": "records", "field": "amount", "max_value": "123456789"}]},
    {"row_rules": [{"type": "conditional_required", "table": "records",
        "when": {"field": "phone", "gte": "123456789"}, "required_fields": ["amount"]}]},
    {"row_rules": [{"type": "conditional_required", "table": "records",
        "when": {"field": "phone", "lte": "123456789"}, "required_fields": ["amount"]}]},
    {"cross_table_rules": [{"type": "aggregate_formula", "table": "records",
        "field": "amount", "expression": "sum('amount')", "expected": "123456789"}]},
])
def test_unbound_rule_bounds_are_rejected_before_mutation(tmp_path, rules):
    from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path

    path = tmp_path / "rules.yaml"
    path.write_text(json.dumps(rules))
    rows = {"records": [{"phone": 0, "amount": 2}]}
    with pytest.raises(BusinessRuleContractError) as error:
        apply_and_validate_business_rules_from_path(
            rows, path, seed=17, mode="negative", invalid_ratio=1,
        )
    assert "123456789" not in str(error.value)
    assert rows == {"records": [{"phone": 0, "amount": 2}]}


def test_aggregate_count_expected_has_no_numeric_measure_exception():
    spec = _spec()
    spec.business_rules = BusinessRules.model_validate({"cross_table_rules": [{
        "type": "aggregate_formula", "table": "records", "field": "*",
        "expression": "count()", "expected": "123456789",
    }]})
    with pytest.raises(BusinessRuleContractError, match="sensitive value"):
        validate_business_rules_for_spec(spec.business_rules, spec)
