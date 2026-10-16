"""Ordinary synthetic rules are portable across interfaces and exact numeric types."""

from decimal import Decimal, localcontext
import json

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation import generate_dataset
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.io.readers import load_dataset_rows
from test_data_agent.validation import validate_dataset
from test_data_agent.rules.models import BusinessRules
from test_data_agent.rules.business_config import make_business_rules_applier


def spec_with_rules():
    def field(name, low, high):
        return {
            "name": name,
            "data_type": "decimal",
            "semantic_type": "numeric_measure",
            "distribution": {
                "kind": "decimal_range",
                "precision": 38,
                "scale": 16,
                "min": low,
                "max": high,
            },
        }

    return DatasetSpec.model_validate(
        {
            "entities": [
                {
                    "name": "items",
                    "row_count": 3,
                    "fields": [
                        field(
                            "base_amount",
                            "9007199254740993.125",
                            "9007199254740993.125",
                        ),
                        field("total", "0", "99999999999999999"),
                    ],
                }
            ],
            "business_rules": {
                "row_rules": [
                    {
                        "type": "formula",
                        "table": "items",
                        "field": "total",
                        "expression": "base_amount * 0.5",
                    }
                ]
            },
        }
    )


def test_embedded_rules_apply_once_and_use_exact_context_independent_arithmetic():
    spec = spec_with_rules()
    for precision in (4, 28, 70):
        with localcontext() as context:
            context.prec = precision
            rows = generate_dataset(spec, seed=7)
            assert rows["items"][0]["total"] == Decimal(
                "4503599627370496.5625000000000000"
            )
            assert validate_dataset(rows, spec).valid
    altered = {"items": [dict(row) for row in rows["items"]]}
    altered["items"][0]["total"] = Decimal("4503599627370496.5625000000000001")
    assert not validate_dataset(altered, spec).valid
    reloaded = DatasetSpec.model_validate_json(spec.model_dump_json())
    assert not validate_dataset(altered, reloaded).valid


@pytest.mark.parametrize("format_name", ["csv", "json", "parquet", "sql"])
def test_portable_rules_roundtrip_and_manifest(tmp_path, format_name):
    from test_data_agent.core.settings import OutputFormat

    if format_name == "parquet":
        pytest.importorskip("pyarrow")
    spec = spec_with_rules()
    rules = spec.business_rules.model_dump(mode="json")
    rules["row_rules"].append(
        {
            "type": "conditional_required",
            "table": "items",
            "when": {"field": "base_amount", "gte": "9007199254740993.125"},
            "required_fields": ["total"],
        }
    )
    rules["cross_table_rules"] = [
        {
            "type": "aggregate_formula",
            "table": "items",
            "field": "total",
            "expression": "sum('base_amount') * 0.5",
        }
    ]
    spec.business_rules = BusinessRules.model_validate(rules)
    result = generate_dataset_bundle(
        spec,
        output_folder=tmp_path / format_name,
        output_format=OutputFormat(format_name),
        seed=7,
    )
    assert result.validation.valid
    manifest = json.loads(
        (tmp_path / format_name / "generation_manifest.json").read_text()
    )
    assert manifest["business_validation"]["assigned_row_count"] == 3
    from test_data_agent.io.readers import load_dataset_spec

    saved = load_dataset_spec(tmp_path / format_name / "dataset_spec.yaml")
    assert validate_dataset(load_dataset_rows(tmp_path / format_name), saved).valid


def test_native_decimal_formula_and_unrelated_constraints():
    spec = spec_with_rules()
    spec.business_rules = None
    spec.constraints = [
        dict(
            type="formula",
            entity="items",
            fields=["total"],
            expression="base_amount / 2",
            confidence=1,
        )
    ]
    # Assignment validation normalizes the typed constraint list at the boundary.
    spec = DatasetSpec.model_validate(spec.model_dump())
    rows = generate_dataset(spec, seed=7)
    assert rows["items"][0]["total"] == Decimal("4503599627370496.5625000000000000")
    assert validate_dataset(rows, spec).valid


def test_business_decimal_conditions_bounds_and_aggregates():
    spec = spec_with_rules()
    spec.business_rules = BusinessRules.model_validate(
        {
            "field_rules": [
                {
                    "table": "items",
                    "field": "total",
                    "min_value": "4503599627370496.5625",
                    "max_value": "4503599627370496.5625",
                }
            ],
            "row_rules": [
                {
                    "type": "formula",
                    "table": "items",
                    "field": "total",
                    "expression": "base_amount * 0.5",
                },
                {
                    "type": "conditional_required",
                    "table": "items",
                    "when": {"field": "base_amount", "gte": "9007199254740993.125"},
                    "required_fields": ["total"],
                },
            ],
            "cross_table_rules": [
                {
                    "type": "aggregate_formula",
                    "table": "items",
                    "field": "total",
                    "expression": "sum('base_amount') * 0.5",
                }
            ],
        }
    )
    rows = generate_dataset(spec, seed=7)
    assert validate_dataset(rows, spec).valid


def test_check_rules_and_bad_exports_do_not_repair_rows(tmp_path):
    from test_data_agent.io.writers import write_dataset_rows
    from test_data_agent.core.settings import OutputFormat

    spec = spec_with_rules()
    rows = generate_dataset(spec, seed=7)
    rows["items"][0]["total"] = Decimal("1")
    with pytest.raises(ValueError, match="business-rule"):
        write_dataset_rows(rows, OutputFormat.JSON, tmp_path, spec=spec)
    assert rows["items"][0]["total"] == Decimal("1")
    assert list(tmp_path.iterdir()) == []


def test_external_rules_become_portable_for_revalidation():
    spec = spec_with_rules()
    rules = spec.business_rules
    spec.business_rules = None
    rows = generate_dataset(spec, seed=7)
    report = make_business_rules_applier(rules)(rows, 7, spec)
    assert report.valid
    assert spec.business_rules == rules
    assert validate_dataset(rows, spec).valid


def test_cli_mcp_and_validation_use_the_same_embedded_rules(tmp_path, monkeypatch):
    from test_data_agent.cli import main
    import test_data_agent.mcp_generator_server as server

    spec = spec_with_rules()
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    assert (
        main(
            [
                "generate",
                str(source),
                "--output",
                str(tmp_path / "cli"),
                "--format",
                "json",
                "--seed",
                "7",
            ]
        )
        == 0
    )
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    result = server.generate_dataset("spec.json", "mcp", output_format="json", seed=7)
    assert result["validation"]["valid"]
    assert load_dataset_rows(tmp_path / "cli") == load_dataset_rows(tmp_path / "mcp")
    saved_spec = next((tmp_path / "mcp").glob("dataset_spec.*"))
    checked = server.validate_dataset(str(saved_spec.relative_to(tmp_path)), "mcp")
    assert checked["validation"]["business_validation"]["valid"]
    assert main(["validate", str(source), str(tmp_path / "cli")]) == 0


def test_agent_reviewed_spec_preserves_embedded_rules(tmp_path):
    import hashlib
    import yaml
    from test_data_agent.agent import (
        plan_agent_request,
        inspect_agent_workspace,
        approve_agent_workspace,
    )
    from test_data_agent.agent_contracts import AgentRequest
    from test_data_agent.io.artifacts import validate_generation_bundle

    source = tmp_path / "input.csv"
    source.write_text("base_amount,total\n2,0\n3,1\n")
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type="csv",
            source_path=source,
            table_name="items",
            workspace=workspace,
            count=3,
            seed=7,
            output_format="json",
        )
    )
    spec = spec_with_rules()
    (workspace / "dataset_spec.yaml").write_text(
        yaml.safe_dump(spec.model_dump(mode="json"))
    )
    spec.generation_settings.seed = 7
    spec.generation_settings.output_format = "json"
    (workspace / "dataset_spec.yaml").write_text(
        yaml.safe_dump(spec.model_dump(mode="json"))
    )
    reviewed = inspect_agent_workspace(workspace)
    approve_agent_workspace(
        workspace, reviewed_spec_sha256=reviewed.review.current_spec_sha256
    )
    assert validate_dataset(load_dataset_rows(workspace / "generated"), spec).valid
    manifest = json.loads(
        (workspace / "generated" / "generation_manifest.json").read_text()
    )
    assert manifest["business_validation"]["assigned_row_count"] == 3
    business_report = workspace / "generated" / "business_validation_report.json"
    assert manifest["reproducibility"]["output_sha256"][business_report.name] == (
        hashlib.sha256(business_report.read_bytes()).hexdigest()
    )
    validate_generation_bundle(workspace / "generated")
    business_report.unlink()
    with pytest.raises(ValueError, match="generation bundle is incomplete or invalid"):
        validate_generation_bundle(workspace / "generated")


@pytest.mark.parametrize("kind", ["sum", "avg", "count"])
@pytest.mark.parametrize("format_name", ["csv", "json", "parquet", "sql"])
def test_native_decimal_aggregate_rounding_and_revalidation(tmp_path, kind, format_name):
    from test_data_agent.core.field import FieldSpec
    from test_data_agent.core.entity import EntitySpec
    from test_data_agent.core.constraint import Constraint

    spec = spec_with_rules()
    spec.business_rules = None
    parent = EntitySpec(
        name="parents",
        row_count=2,
        primary_key="pid",
        fields=[
            FieldSpec(name="pid", data_type="string", is_identifier=True),
            spec.entities[0].field("total").model_copy(deep=True),
        ],
    )
    child = EntitySpec(
        name="children",
        row_count=3,
        fields=[
            FieldSpec(name="pid", data_type="string", is_identifier=True),
            spec.entities[0].field("base_amount").model_copy(deep=True),
        ],
    )
    spec.entities = [parent, child]
    spec.relationships = [
        {
            "parent_entity": "parents",
            "parent_field": "pid",
            "child_entity": "children",
            "child_field": "pid",
            "confidence": 1,
        }
    ]
    spec.constraints = [
        Constraint(
            type="aggregate_mapping",
            entity="parents",
            fields=["total"],
            target_entity="children",
            target_field="base_amount",
            aggregate=kind,
            confidence=1,
        )
    ]
    spec = DatasetSpec.model_validate(spec.model_dump())
    rows = generate_dataset(spec, seed=7)
    assert validate_dataset(rows, spec).valid
    expected = (
        Decimal("18014398509481986.2500000000000000")
        if kind == "sum"
        else Decimal("9007199254740993.1250000000000000")
        if kind == "avg"
        else Decimal("2")
    )
    assert rows["parents"][0]["total"] == expected
    from test_data_agent.core.settings import OutputFormat

    generate_dataset_bundle(
        spec, output_folder=tmp_path / kind, seed=7, output_format=OutputFormat(format_name)
    )
    assert validate_dataset(load_dataset_rows(tmp_path / kind), spec).valid


def test_embedded_business_budget_rejects_before_allocation(monkeypatch):
    import test_data_agent.generation.entity_generator as module

    spec = spec_with_rules()
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "1")
    monkeypatch.setattr(
        module,
        "create_faker",
        lambda *_: pytest.fail("allocated before rule preflight"),
    )
    with pytest.raises(ValueError, match="estimated evaluations"):
        generate_dataset(spec, seed=7)


@pytest.mark.parametrize(
    "mode,count",
    [("valid", 3), ("edge", 3), ("load_test", 30), ("negative", 3), ("mixed", 3)],
)
def test_embedded_rules_in_every_mode(mode, count):
    spec = spec_with_rules()
    spec.generation_settings.mode = mode
    spec.generation_settings.invalid_ratio = 0.5 if mode == "mixed" else 0
    reports = []
    rows = generate_dataset(spec, seed=7, business_reports=reports)
    assert len(rows["items"]) == count
    assert reports[0].expectations_met
    assert reports[0].results[0].assigned_row_count == count
    materialized = spec.model_copy(deep=True)
    materialized.entities[0].row_count = count
    materialized.generation_settings.load_multiplier = 1
    assert validate_dataset(rows, materialized).valid == (
        mode not in {"negative", "mixed"}
    )


@pytest.mark.parametrize(
    "expression,expected", [("1.005", "1.01"), ("-1.005", "-1.01"), ("1 / 3", "0.33")]
)
def test_decimal_formula_rounds_once_half_up(expression, expected):
    spec = spec_with_rules()
    target = spec.entities[0].field("total")
    target.distribution = {
        "kind": "decimal_range",
        "precision": 5,
        "scale": 2,
        "min": "-999.99",
        "max": "999.99",
    }
    spec.business_rules.row_rules[0].expression = expression
    rows = generate_dataset(spec, seed=7)
    assert rows["items"][0]["total"] == Decimal(expected)
    assert validate_dataset(rows, spec).valid
    spec.business_rules.row_rules[0].expression = "999.995"
    with pytest.raises(ValueError, match="formula"):
        generate_dataset(spec, seed=7)


def test_explicit_decimal_tolerance_and_check_mode_survive_reload():
    spec = spec_with_rules()
    rows = generate_dataset(spec, seed=7)
    rows["items"][0]["total"] = Decimal("4503599627370496.5625000000000001")
    spec.business_rules.row_rules[0].tolerance = 0.000001
    spec.business_rules.row_rules[0].mode = "check"
    saved = DatasetSpec.model_validate_json(spec.model_dump_json())
    assert validate_dataset(rows, saved).valid


def test_business_rules_cannot_be_disabled_by_optional_validation_settings():
    from test_data_agent.core.settings import ValidationSettings

    spec = spec_with_rules()
    spec.validation_settings = ValidationSettings(
        validate_schema=False,
        validate_relationships=False,
        validate_constraints=False,
        validate_privacy=False,
    )
    rows = generate_dataset(spec, seed=7)
    rows["items"][0]["total"] = Decimal("1")
    assert not validate_dataset(rows, spec).valid


@pytest.mark.parametrize("mode", ["valid", "edge", "load_test", "negative", "mixed"])
def test_external_and_embedded_rules_share_generation(tmp_path, mode):
    spec = spec_with_rules()
    spec.generation_settings.mode = mode
    spec.generation_settings.invalid_ratio = 0.5 if mode == "mixed" else 0
    embedded = generate_dataset_bundle(
        spec, output_folder=tmp_path / "embedded", seed=7
    )
    rules = spec.business_rules
    spec.business_rules = None
    external = generate_dataset_bundle(
        spec,
        output_folder=tmp_path / "external",
        seed=7,
        business_rules_applier=make_business_rules_applier(rules),
    )
    assert load_dataset_rows(tmp_path / "embedded") == load_dataset_rows(
        tmp_path / "external"
    )
    assert embedded.business_validation == external.business_validation


def test_cli_external_rules_negative_match_mcp(tmp_path, monkeypatch):
    import yaml
    from test_data_agent.cli import main
    import test_data_agent.mcp_generator_server as server

    spec = spec_with_rules()
    spec.generation_settings.mode = "negative"
    rules = spec.business_rules
    spec.business_rules = None
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(yaml.safe_dump(rules.model_dump(mode="json")))
    assert (
        main(
            [
                "generate",
                str(source),
                "--business-rules",
                str(rules_path),
                "--output",
                str(tmp_path / "cli"),
                "--format",
                "json",
                "--seed",
                "7",
            ]
        )
        == 1
    )
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    result = server.generate_dataset(
        "spec.json",
        "mcp",
        output_format="json",
        seed=7,
        business_rules_path="rules.yaml",
    )
    assert result["business_validation"]["unexpected_violation_count"] == 0
    assert load_dataset_rows(tmp_path / "cli") == load_dataset_rows(tmp_path / "mcp")


def test_decimal_nullable_scenario_and_allowed_values():
    spec = spec_with_rules()
    spec.entities[0].field("total").nullable = True
    spec.business_rules = BusinessRules.model_validate(
        {
            "field_rules": [
                {"table": "items", "field": "total", "allowed_values": [None]}
            ],
            "scenarios": [
                {
                    "name": "missing_measure",
                    "weight": 1,
                    "field_values": {"items": {"total": None}},
                }
            ],
        }
    )
    rows = generate_dataset(spec, seed=7)
    assert all(row["total"] is None for row in rows["items"])
    assert validate_dataset(rows, spec).valid


def test_cli_validation_external_rules_checks_without_assignment(tmp_path):
    import yaml
    from test_data_agent.cli import main

    spec = spec_with_rules()
    rows = generate_dataset(spec, seed=7)
    rows["items"][0]["total"] = Decimal("1")
    rules = spec.business_rules
    spec.business_rules = None
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(yaml.safe_dump(rules.model_dump(mode="json")))
    folder = tmp_path / "rows"
    folder.mkdir()
    data_path = folder / "items.json"
    data_path.write_text(json.dumps(rows["items"], default=str))
    before = data_path.read_bytes()
    assert (
        main(
            ["validate", str(source), str(folder), "--business-rules", str(rules_path)]
        )
        == 1
    )
    assert data_path.read_bytes() == before


def test_decimal_comparison_literals_do_not_use_single_row_storage_shape():
    spec = spec_with_rules()
    for field in spec.entities[0].fields:
        field.distribution = {'kind': 'decimal_range', 'precision': 3, 'scale': 0, 'min': '999', 'max': '999'}
    spec.business_rules = BusinessRules.model_validate({
        'field_rules': [{'table': 'items', 'field': 'total', 'min_value': '998.9999'}],
        'row_rules': [{'type': 'conditional_required', 'table': 'items',
                       'when': {'field': 'total', 'gte': '998.9999'}, 'required_fields': ['base_amount']}],
        'cross_table_rules': [{'type': 'aggregate_formula', 'table': 'items', 'field': 'total',
                               'expression': "sum('total')", 'expected': '2997'}],
    })
    rows = generate_dataset(spec, seed=7)
    assert validate_dataset(rows, DatasetSpec.model_validate_json(spec.model_dump_json())).valid
