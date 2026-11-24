import math
from pathlib import Path
from typing import Any

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.io.readers import load_dataset_rows
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.rules.expressions import aggregate, numbers_close, safe_eval
from test_data_agent.rules.models import business_rules_from_dict
from test_data_agent.rules.validation import validate_business_rules
from test_data_agent.validation import validate_dataset


LARGE_INTEGER = 2**53


@pytest.mark.parametrize("as_csv", [False, True])
@pytest.mark.parametrize("difference", [0, 1])
def test_integer_formula_preserves_values_above_float_precision(
    as_csv: bool, difference: int,
) -> None:
    spec = DatasetSpec.model_validate({
        "entities": [{
            "name": "items", "row_count": 1,
            "fields": [{"name": name, "data_type": "integer"} for name in ("a", "b")],
        }],
        "constraints": [{
            "type": "formula", "entity": "items", "fields": ["b"],
            "expression": "a", "confidence": 1,
        }],
    })
    row: dict[str, Any] = {"a": LARGE_INTEGER, "b": LARGE_INTEGER + difference}
    if as_csv:
        row = {name: str(value) for name, value in row.items()}

    report = validate_dataset({"items": [row]}, spec)

    assert report.valid is (difference == 0)


@pytest.mark.parametrize("as_csv", [False, True])
@pytest.mark.parametrize("difference", [0, 1])
def test_integer_sum_is_exact_and_ignores_nullable_csv_blanks(
    tmp_path: Path, as_csv: bool, difference: int,
) -> None:
    spec = DatasetSpec.model_validate({
        "entities": [{
            "name": "parents", "row_count": 1,
            "fields": [
                {"name": "id", "data_type": "integer", "is_identifier": True},
                {"name": "total", "data_type": "integer"},
            ],
        }, {
            "name": "children", "row_count": 3,
            "fields": [
                {"name": "parent_id", "data_type": "integer"},
                {"name": "amount", "data_type": "integer", "nullable": True},
            ],
        }],
        "relationships": [{
            "parent_entity": "parents", "parent_field": "id",
            "child_entity": "children", "child_field": "parent_id", "confidence": 1,
        }],
        "constraints": [{
            "type": "aggregate_mapping", "entity": "parents", "fields": ["total"],
            "target_entity": "children", "target_field": "amount",
            "aggregate": "sum", "confidence": 1,
        }],
    })
    rows: dict[str, list[dict[str, Any]]] = {
        "parents": [{"id": 1, "total": LARGE_INTEGER + 1 + difference}],
        "children": [{"parent_id": 1, "amount": value} for value in (LARGE_INTEGER, 1, None)],
    }
    if as_csv:
        for entity, entity_rows in rows.items():
            (tmp_path / f"{entity}.csv").write_text(rows_to_csv(entity_rows))
        rows = load_dataset_rows(tmp_path)

    assert validate_dataset(rows, spec).valid is (difference == 0)


def test_business_aggregate_keeps_integer_precision() -> None:
    rules = business_rules_from_dict({"cross_table_rules": [{
        "type": "aggregate_formula", "table": "items", "field": "amount",
        "expression": 'sum("amount")', "expected": LARGE_INTEGER + 1,
    }]})
    rows = {"items": [{"amount": LARGE_INTEGER}, {"amount": 1}, {"amount": None}]}

    assert validate_business_rules(rows, rules).valid

    rules.cross_table_rules[0].expected = LARGE_INTEGER
    assert not validate_business_rules(rows, rules).valid


@pytest.mark.parametrize("actual", [LARGE_INTEGER + 1, str(LARGE_INTEGER + 1)])
@pytest.mark.parametrize("expected", [LARGE_INTEGER, str(LARGE_INTEGER), float(LARGE_INTEGER)])
def test_numeric_comparison_does_not_round_before_subtraction(actual: Any, expected: Any) -> None:
    assert not numbers_close(actual, expected)
    assert numbers_close(actual, expected, tolerance=1)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, "inf", "nan", "invalid"])
def test_nonfinite_or_invalid_values_cannot_pass_aggregate_validation(value: Any) -> None:
    rules = business_rules_from_dict({"cross_table_rules": [{
        "type": "aggregate_formula", "table": "items", "field": "amount",
        "expression": 'sum("amount")', "expected": 0,
    }]})

    assert not numbers_close(value, value)
    assert not validate_business_rules({"items": [{"amount": value}]}, rules).valid


def test_float_comparison_retains_tolerance_and_count_is_an_integer() -> None:
    assert numbers_close(1.0, 1.0000005)
    assert not numbers_close(1.0, 1.000002)
    rows = [{"value": 1}, {"value": 2}]
    assert type(aggregate("*", rows)) is int
    assert type(safe_eval("count()", {"rows": rows})) is int
