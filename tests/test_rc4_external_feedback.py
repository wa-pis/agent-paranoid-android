"""Fictional regressions from the RC4 external feedback."""

from decimal import Decimal
import random

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.distribution import NumericShapeDistribution
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.field import FieldProfile, FieldSpec
from test_data_agent.generation.entity_generator import generate_dataset, ranged_number
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.profiling.numeric_shape import shape_prevalence
from test_data_agent.rules.business_config import apply_and_validate_business_rules
from test_data_agent.rules.conditions import Condition, condition_matches
from test_data_agent.rules.models import BusinessRules
from test_data_agent.safety import (
    SpecSafetyError,
    assert_spec_safe,
    validate_generated_row_privacy,
)
from test_data_agent.validation.schema_validator import validate_schema


def measure(**changes):
    return FieldSpec.model_validate(
        {
            "name": "amount",
            "data_type": "decimal",
            "semantic_type": "numeric_measure",
            "distribution": {
                "kind": "decimal_range",
                "precision": 38,
                "scale": 16,
                "min": "0.0000000000000001",
                "max": "9.9999999999999999",
            },
            **changes,
        }
    )


def test_reviewed_decimal_measure_is_exact_and_not_automatic():
    field = measure()
    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="items",
                row_count=20,
                fields=[
                    FieldProfile(
                        name="amount",
                        data_type="decimal",
                        decimal_precision=38,
                        decimal_scale=16,
                    ),
                ],
            )
        ]
    )
    with pytest.raises(ValueError, match="--decimal-fields"):
        infer_dataset_spec(profile)
    spec = infer_dataset_spec(profile, decimal_fields={"items.amount": field})
    rows = generate_dataset(spec, seed=71)
    assert all(isinstance(row["amount"], Decimal) for row in rows["items"])
    assert validate_schema(rows, spec) == []
    assert validate_generated_row_privacy(rows, spec) == []
    serialized = {"items": [{"amount": str(row["amount"])} for row in rows["items"]]}
    assert (
        validate_generated_row_privacy(serialized, spec, parse_numeric_strings=True)
        == []
    )
    with pytest.raises(ValueError, match="precision and scale"):
        infer_dataset_spec(
            profile,
            decimal_fields={
                "items.amount": measure(
                    distribution={
                        "kind": "decimal_range",
                        "precision": 12,
                        "scale": 2,
                        "min": "0",
                        "max": "1",
                    }
                )
            },
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"sensitive": True},
        {"is_identifier": True},
        {"name": "phone"},
        {"data_type": "string"},
    ],
)
def test_measure_never_overrides_sensitive_or_identifier_fields(changes):
    with pytest.raises(ValueError):
        measure(**changes)


def test_default_decimal_sensitive_bounds_remain_rejected():
    field = measure(
        semantic_type=None,
        distribution={
            "kind": "decimal_range",
            "precision": 38,
            "scale": 16,
            "min": "12345678901.2345678901234567",
            "max": "12345678901.2345678901234567",
        },
    )
    spec = DatasetSpec(
        schema_version="1.1",
        entities=[EntitySpec(name="items", row_count=1, fields=[field])],
    )
    with pytest.raises(SpecSafetyError):
        assert_spec_safe(spec)


def test_prevalence_retains_negative_magnitudes_and_subunits():
    metadata = shape_prevalence(
        {"zero_count": 10, "subunit_count": 89, "min_subunit_magnitude": -12}, 100
    )
    shape = NumericShapeDistribution(max_abs_magnitude=2, has_positive=True, **metadata)
    rng = random.Random(71)
    values = [ranged_number(None, shape, {}, rng, 0, 1000) for _ in range(1000)]
    assert 800 < sum(0 < value < 1 for value in values) < 950
    assert 50 < values.count(0) < 150
    with pytest.raises(ValueError, match="counts"):
        shape_prevalence({"zero_count": 70, "subunit_count": 40}, 100)
    zero = NumericShapeDistribution(max_abs_magnitude=0, zero_ratio=1)
    assert ranged_number(None, zero, {}, rng, 0, 1000) == 0


@pytest.mark.parametrize(
    "payload,good,bad",
    [
        ({"equals": None}, None, 1),
        ({"not_equals": None}, 1, None),
        ({"gte": 2, "lte": 4}, 3, 5),
        ({"in_values": [1, 2]}, 2, None),
    ],
)
def test_conditions_roundtrip_null_and_range(payload, good, bad):
    condition = Condition(field="value", **payload)
    restored = Condition.model_validate_json(condition.model_dump_json())
    assert condition_matches({"value": good}, restored)
    assert not condition_matches({"value": bad}, restored)


def test_formulas_report_assignment_and_check_without_mutating():
    rows = {"items": [{"quantity": 2, "total": 1}]}

    def rules(mode):
        return BusinessRules.model_validate(
            {
                "row_rules": [
                    {
                        "type": "formula",
                        "mode": mode,
                        "table": "items",
                        "field": "total",
                        "expression": "quantity * 3",
                    }
                ]
            }
        )

    check = apply_and_validate_business_rules(
        rows, rules("check"), seed=1, mode="valid", invalid_ratio=0
    )
    assert rows["items"][0]["total"] == 1
    assert not check.valid and check.results[0].assigned_row_count == 0
    assign = apply_and_validate_business_rules(
        rows, rules("assign"), seed=1, mode="valid", invalid_ratio=0
    )
    assert rows["items"][0]["total"] == 6
    assert assign.valid and assign.results[0].assigned_row_count == 1
    assert assign.results[0].application == "assign"


def test_dbapi_decimal_metadata_uses_precision_and_scale():
    from types import SimpleNamespace
    from test_data_agent.sql_query_adapters import _trino_description_column

    column = _trino_description_column(
        ("amount", SimpleNamespace(name="decimal"), None, None, 38, 16, True)
    )
    assert column.data_type == "decimal(38,16)"
    from test_data_agent.sql_query_profiling import SqlQueryProfileError

    with pytest.raises(SqlQueryProfileError):
        _trino_description_column(
            ("amount", SimpleNamespace(name="decimal"), None, None, 38, 39, True)
        )


def test_formula_assignment_cannot_silently_exceed_reviewed_domain():
    from test_data_agent.rules.business_config import make_business_rules_applier

    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=1,
                fields=[
                    FieldSpec(name="quantity", data_type="integer"),
                    FieldSpec(
                        name="total",
                        data_type="float",
                        distribution={
                            "kind": "numeric",
                            "min_value": 0,
                            "max_value": 5,
                        },
                    ),
                ],
            )
        ]
    )
    rules = BusinessRules.model_validate(
        {
            "row_rules": [
                {
                    "type": "formula",
                    "table": "items",
                    "field": "total",
                    "expression": "quantity * 3",
                }
            ]
        }
    )
    report = make_business_rules_applier(rules)(
        {"items": [{"quantity": 2, "total": 1}]}, 1, spec
    )
    assert report.distribution_bounds_checked_count == 1
    assert report.distribution_bounds_violation_count == 1


def test_explicit_mode_override_clears_only_saved_invalid_ratio(tmp_path):
    from test_data_agent.io.workflows import generate_dataset_bundle

    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=2,
                fields=[FieldSpec(name="quantity", data_type="integer")],
            )
        ],
        generation_settings={"mode": "mixed", "invalid_ratio": 0.1},
    )
    result = generate_dataset_bundle(spec, output_folder=tmp_path / "edge", mode="edge")
    assert result.validation.valid
    with pytest.raises(ValueError):
        generate_dataset_bundle(
            spec, output_folder=tmp_path / "bad", mode="edge", invalid_ratio=0.1
        )


def test_sensitive_privacy_policy_vetoes_numeric_measure():
    spec = DatasetSpec(
        schema_version="1.1",
        entities=[EntitySpec(name="items", row_count=1, fields=[measure()])],
        privacy_rules=[
            {"entity": "items", "field": "amount", "classification": "sensitive"}
        ],
    )
    with pytest.raises(SpecSafetyError, match="sensitive|privacy classification"):
        assert_spec_safe(spec)


def test_sql_business_rules_apply_and_check_atomically(tmp_path, capsys):
    from test_data_agent.cli import main

    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=2,
                fields=[
                    FieldSpec(
                        name="quantity",
                        data_type="integer",
                        distribution={
                            "kind": "numeric",
                            "min_value": 2,
                            "max_value": 2,
                        },
                    ),
                    FieldSpec(
                        name="total",
                        data_type="integer",
                        distribution={
                            "kind": "numeric",
                            "min_value": 1,
                            "max_value": 1,
                        },
                    ),
                ],
            )
        ]
    )
    path = tmp_path / "spec.json"
    path.write_text(spec.model_dump_json())
    rules = tmp_path / "rules.json"
    payload = {
        "row_rules": [
            {
                "type": "formula",
                "table": "items",
                "field": "total",
                "expression": "quantity * 3",
            }
        ]
    }
    import json

    rules.write_text(json.dumps(payload))
    output = tmp_path / "result.sql"
    command = [
        "export-postgres-sql",
        str(path),
        "--business-rules",
        str(rules),
        "--output",
        str(output),
    ]
    assert main(command) == 0
    saved = output.read_text()
    assert "(2, 6)" in saved
    payload["row_rules"][0]["mode"] = "check"
    rules.write_text(json.dumps(payload))
    assert main([*command, "--overwrite"]) != 0
    assert output.read_text() == saved


def test_sql_load_count_is_materialized_once(tmp_path):
    from test_data_agent.cli import main

    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="items",
                row_count=2,
                fields=[
                    FieldSpec(
                        name="quantity",
                        data_type="integer",
                        distribution={
                            "kind": "numeric",
                            "min_value": 2,
                            "max_value": 2,
                        },
                    ),
                ],
            )
        ],
        generation_settings={"mode": "load_test"},
    )
    path = tmp_path / "spec.json"
    path.write_text(spec.model_dump_json())
    output = tmp_path / "load.sql"
    command = ["export-postgres-sql", str(path), "--output", str(output)]
    assert main(command) == 0
    assert output.read_text().count("(2)") == 20
    assert main([*command, "--count", "3", "--overwrite"]) == 0
    assert output.read_text().count("(2)") == 3


def test_infer_cli_reviewed_decimal_mapping(tmp_path):
    import json
    from test_data_agent.cli import main

    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="items",
                row_count=2,
                fields=[
                    FieldProfile(
                        name="amount",
                        data_type="decimal",
                        decimal_precision=38,
                        decimal_scale=16,
                    ),
                ],
            )
        ]
    )
    source = tmp_path / "profile.json"
    source.write_text(profile.model_dump_json())
    overrides = tmp_path / "ranges.json"
    overrides.write_text(
        json.dumps({"items.amount": measure().model_dump(mode="json")})
    )
    output = tmp_path / "spec.json"
    assert (
        main(
            [
                "infer-spec",
                str(source),
                "--decimal-fields",
                str(overrides),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    restored = DatasetSpec.model_validate_json(output.read_text())
    assert restored.entities[0].fields[0].semantic_type == "numeric_measure"


def test_legacy_condition_null_defaults_do_not_change_comparison():
    condition = Condition.model_validate(
        {"field": "value", "equals": None, "not_equals": 2, "in_values": None}
    )
    assert condition_matches({"value": 3}, condition)
    assert not condition_matches({"value": 2}, condition)
    assert condition_matches({"value": None}, condition)


def test_invalid_decimal_mapping_error_never_echoes_values(tmp_path, capsys):
    from test_data_agent.cli import main

    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="items",
                row_count=1,
                fields=[
                    FieldProfile(
                        name="amount",
                        data_type="decimal",
                        decimal_precision=38,
                        decimal_scale=16,
                    ),
                ],
            )
        ]
    )
    source = tmp_path / "profile.json"
    source.write_text(profile.model_dump_json())
    overrides = tmp_path / "ranges.yaml"
    marker = "SYNTHETIC_REJECTED_VALUE_MARKER"
    overrides.write_text("- " + marker)
    output = tmp_path / "spec.json"
    assert (
        main(
            [
                "infer-spec",
                str(source),
                "--decimal-fields",
                str(overrides),
                "--output",
                str(output),
            ]
        )
        != 0
    )
    captured = capsys.readouterr()
    assert marker not in captured.out + captured.err
    assert not output.exists()


@pytest.mark.parametrize("adapter", ["postgres", "trino"])
@pytest.mark.parametrize("zero_only", [False, True])
def test_sql_numeric_prevalence_survives_profile_inference(adapter, zero_only):
    from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery
    from test_data_agent.sql_query_profiling import (
        QueryResultColumn,
        profile_validated_query,
    )

    plan = ValidatedSqlQuery(
        adapter=SqlQueryAdapter(adapter),
        source_id="warehouse",
        entity_name="items",
        table_parts=("public", "items")
        if adapter == "postgres"
        else ("lake", "safe", "items"),
        output_fields=("amount",),
        fingerprint="a" * 64,
        sql='SELECT "amount" FROM "public"."items"',
    )

    def fetch(query):
        if "non_null_count" not in query.sql:
            return [{"row_count": 20}]
        assert "AS subunit_count" in query.sql
        return [
            {
                "row_count": 20,
                "non_null_count": 20,
                "distinct_count": 1 if zero_only else 20,
                "has_negative": not zero_only,
                "has_positive": False,
                "max_abs_magnitude": None if zero_only else -8,
                "zero_count": 20 if zero_only else 0,
                "subunit_count": 0 if zero_only else 20,
                "min_subunit_magnitude": None if zero_only else -12,
            }
        ]

    profile = profile_validated_query(
        plan,
        describe_query=lambda _: [
            QueryResultColumn(
                "amount", "double precision" if adapter == "postgres" else "double"
            )
        ],
        fetch_query=fetch,
    )
    field = profile.entities[0].fields[0]
    assert field.distribution["zero_ratio"] == (1 if zero_only else 0)
    spec = infer_dataset_spec(profile)
    values = [row["amount"] for row in generate_dataset(spec, seed=7)["items"]]
    assert (
        all(value == 0 for value in values)
        if zero_only
        else all(-1e-6 < value < 0 for value in values)
    )


@pytest.mark.parametrize("format_name", ["csv", "json", "parquet"])
def test_reviewed_measure_bundle_exports_and_revalidates(tmp_path, format_name):
    if format_name == "parquet":
        pytest.importorskip("pyarrow")
    from test_data_agent.core.settings import OutputFormat
    from test_data_agent.io.workflows import generate_dataset_bundle
    from test_data_agent.io.readers import load_dataset_rows
    from test_data_agent.validation import validate_dataset

    spec = DatasetSpec(
        schema_version="1.1",
        entities=[EntitySpec(name="items", row_count=20, fields=[measure()])],
    )
    folder = tmp_path / format_name
    result = generate_dataset_bundle(
        spec, output_folder=folder, output_format=OutputFormat(format_name), seed=71
    )
    assert result.validation.valid
    assert validate_dataset(load_dataset_rows(folder), spec).valid
