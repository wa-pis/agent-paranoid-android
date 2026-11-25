"""Keep the optimized privacy walk equivalent to its original row policy."""

import json
import random
import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

import test_data_agent.safety as safety
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.decimal_units import value_matches_decimal
from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.privacy import (
    SENSITIVE_NAME_PARTS,
    SENSITIVE_SEMANTIC_TYPES,
    infer_sensitive_value_type,
    is_sensitive_field,
)
from test_data_agent.csv_profiler import parse_float, parse_int


def _original_privacy_validation(
    rows_by_entity: dict[str, list[Any]],
    spec: DatasetSpec,
    *,
    parse_numeric_strings: bool = False,
) -> list[str]:
    # Freeze the 1.7.1 walk, including DECIMAL and identifier precedence.
    for entity in spec.entities:
        field_policies = [
            (field, field.sensitive or is_sensitive_field(field.name, field.semantic_type))
            for field in entity.fields
        ]
        for row in rows_by_entity.get(entity.name, []):
            if not isinstance(row, Mapping):
                return ["row privacy validation requires object rows"]
            for field, sensitive in field_policies:
                value = row.get(field.name)
                if value in (None, ""):
                    continue
                if isinstance(value, (dict, list, tuple)):
                    return ["row privacy validation requires scalar fields"]
                if parse_numeric_strings and isinstance(value, str) and (
                    field.data_type == FieldType.INTEGER and parse_int(value) is not None
                    or field.data_type == FieldType.FLOAT and parse_float(value) is not None
                ):
                    continue
                if (
                    field.semantic_type == "numeric_measure"
                    and not safety._spec_field_is_sensitive(spec, entity.name, field.name)
                    and field.data_type == FieldType.DECIMAL
                    and (isinstance(value, Decimal) or parse_numeric_strings and isinstance(value, str))
                    and isinstance(field.typed_distribution, DecimalRangeDistribution)
                    and value_matches_decimal(
                        value, precision=field.typed_distribution.precision,
                        scale=field.typed_distribution.scale,
                        low=field.typed_distribution.min, high=field.typed_distribution.max,
                    )
                ):
                    continue
                detected = (
                    safety._decimal_sensitive_value_type(value)
                    if field.data_type == FieldType.DECIMAL
                    else infer_sensitive_value_type(value)
                )
                if field.data_type == FieldType.DECIMAL and isinstance(value, Decimal) and detected:
                    return ["generated dataset failed post-solve privacy validation"]
                if field.is_identifier and isinstance(value, str) and re.fullmatch(
                    r"synthetic_-?[0-9]+", value,
                ):
                    continue
                if isinstance(value, str) and (
                    sensitive or detected is not None
                ) and not _original_synthetic_value(value, field.semantic_type or detected):
                    return ["generated dataset failed post-solve privacy validation"]
    return []


def _original_synthetic_value(value: str, value_type: str | None) -> bool:
    if value_type == "email":
        return value.endswith("@example.test")
    if value_type == "phone":
        return value.startswith("+1-202-555-")
    if value_type == "ssn":
        return value.startswith("000-00-")
    return value.startswith("synthetic_")


def _spec(fields: list[FieldSpec]) -> DatasetSpec:
    return DatasetSpec.model_validate({
        "schema_version": "1.1",
        "entities": [{"name": "records", "row_count": 4, "fields": fields}],
    })


def _field(*, name: str, data_type: FieldType, **options: Any) -> FieldSpec:
    if data_type == FieldType.DECIMAL:
        options["distribution"] = {
            "kind": "decimal_range", "precision": 10, "scale": 2,
            "min": "1", "max": "10",
        }
    return FieldSpec(name=name, data_type=data_type, **options)


def _value_cases() -> list[tuple[str, Any]]:
    corpus = json.loads((Path(__file__).parent / "fixtures" / "privacy_detection_cases.json").read_text())
    cases = [(case["id"], "".join(case["parts"])) for case in corpus["value_cases"]]
    cases.extend([
        ("none", None), ("empty", ""), ("whitespace", " \t"),
        ("false", False), ("true", True), ("zero", 0), ("integer", 1234567),
        ("float", 1234567.0), ("nan", float("nan")), ("infinity", float("inf")),
        ("decimal", Decimal("1234567")), ("bytes", b"synthetic_bytes"),
        ("date_object", date(2026, 1, 2)), ("datetime_object", datetime(2026, 1, 2, 3, 4)),
        ("set", {1}), ("frozenset", frozenset({1})),
        ("empty_dict", {}), ("dict", {"nested": "synthetic_nested"}),
        ("empty_list", []), ("list", [None]), ("empty_tuple", ()), ("tuple", (1,)),
        ("numeric_string", "1234567"), ("padded_integer", " 1234567 "),
        ("leading_zero", "01234567"), ("signed_integer", "+1234567"),
        ("float_string", "1234567.0"), ("exponent", "1.234567e6"),
        ("nan_string", "nan"), ("infinity_string", "Infinity"),
        ("iso_date", "2024-02-29"), ("invalid_iso_date", "2024-02-30"),
        ("padded_iso_date", " 2024-02-29 "),
        ("synthetic_text", "synthetic_record_1"),
        ("synthetic_email", "synthetic_record@example.test"),
        ("synthetic_prefix_email", "synthetic_record@example.invalid"),
        ("padded_synthetic", " synthetic_record_1 "),
        ("padded_synthetic_email", " synthetic_record@example.test "),
        ("assignment_before_email", "synthetic_secret=record@example.invalid"),
        ("bearer_before_email", "Bearer record@example.test"),
        ("ssn_before_phone", "000000000"),
        ("unicode_digits", "١٢٣٤٥٦٧"), ("unicode_whitespace", "123\u20034567"),
    ])
    return cases


def _assert_equivalent(case_id: str, rows: dict[str, list[Any]], spec: DatasetSpec, parse: bool) -> None:
    expected = _original_privacy_validation(rows, spec, parse_numeric_strings=parse)
    actual = safety.validate_generated_row_privacy(rows, spec, parse_numeric_strings=parse)
    assert actual == expected, case_id


@pytest.mark.parametrize("parse_numeric_strings", [False, True], ids=["strict", "report"])
def test_privacy_walk_matches_original_for_value_and_field_matrix(parse_numeric_strings):
    fields = [_field(name="payload", data_type=data_type) for data_type in FieldType]
    fields.extend(FieldSpec(name=name, data_type=FieldType.STRING) for name in sorted(SENSITIVE_NAME_PARTS))
    fields.extend(FieldSpec(name=name, data_type=FieldType.STRING)
                  for name in ("contact-email", "first name", "CUSTOMER_EMAIL", "account_id", "order_cc"))
    fields.extend(
        FieldSpec(name="payload", data_type=FieldType.STRING, semantic_type=semantic_type,
                  sensitive=sensitive)
        for semantic_type in [None, "", *sorted(SENSITIVE_SEMANTIC_TYPES), "identifier", "EMAIL", " email "]
        for sensitive in (False, True)
    )
    for field_index, field in enumerate(fields):
        spec = _spec([field])
        for case_id, value in _value_cases():
            _assert_equivalent(f"field_{field_index}:{case_id}", {"records": [{field.name: value}]},
                               spec, parse_numeric_strings)


@pytest.mark.parametrize("parse_numeric_strings", [False, True], ids=["strict", "report"])
def test_privacy_walk_preserves_missing_rows_fields_and_first_error(parse_numeric_strings):
    spec = _spec([FieldSpec(name="payload", data_type=FieldType.STRING)])
    spec.entities.append(spec.entities[0].model_copy(update={"name": "later"}, deep=True))
    cases = [
        ("missing_entity", {}), ("empty_entity", {"records": []}),
        ("missing_field", {"records": [{}]}),
        ("unknown_entity", {"ignored": [None]}),
        ("unknown_field", {"records": [{"extra": [None]}]}),
        ("object_error_first", {"records": [None, {"payload": []}]}),
        ("scalar_error_first", {"records": [{"payload": []}, None]}),
        ("entity_order", {"later": [None], "records": [{"payload": []}]}),
        ("privacy_error_first", {"records": [{"payload": "record@example.invalid"}, None]}),
    ]
    cases.extend((f"non_mapping_{index}", {"records": [value]})
                 for index, value in enumerate([None, "", "synthetic_row", 0, [], (), date(2026, 1, 2)]))
    for case_id, rows in cases:
        _assert_equivalent(case_id, rows, spec, parse_numeric_strings)
    spec.entities[0].fields.append(FieldSpec(name="later", data_type=FieldType.STRING))
    rows = {"records": [{"payload": "record@example.invalid", "later": []}]}
    _assert_equivalent("field_order_privacy_first", rows, spec, parse_numeric_strings)
    spec.entities[0].fields.reverse()
    _assert_equivalent("field_order_scalar_first", rows, spec, parse_numeric_strings)


def test_privacy_walk_observes_spec_and_row_mutations_between_calls():
    spec = _spec([FieldSpec(name="payload", data_type=FieldType.STRING)])
    field = spec.entities[0].fields[0]
    rows = {"records": [{"payload": "ordinary_category"}]}
    assert safety.validate_generated_row_privacy(rows, spec) == []
    field.sensitive = True
    assert safety.validate_generated_row_privacy(rows, spec) == [
        "generated dataset failed post-solve privacy validation"
    ]
    field.sensitive = False
    assert safety.validate_generated_row_privacy(rows, spec) == []
    field.sensitive = True
    rows["records"][0]["payload"] = "synthetic_record@example.test"
    assert safety.validate_generated_row_privacy(rows, spec) == []
    field.semantic_type = "phone"
    assert safety.validate_generated_row_privacy(rows, spec) == [
        "generated dataset failed post-solve privacy validation"
    ]
    field.semantic_type = "email"
    assert safety.validate_generated_row_privacy(rows, spec) == []
    field.sensitive = False
    field.semantic_type = None
    field.name = "contact_email"
    rows["records"][0] = {"contact_email": "ordinary_category"}
    assert safety.validate_generated_row_privacy(rows, spec) == [
        "generated dataset failed post-solve privacy validation"
    ]
    spec.entities[0].fields = [FieldSpec(name="quantity", data_type=FieldType.INTEGER)]
    rows["records"][0] = {"quantity": "1234567"}
    assert safety.validate_generated_row_privacy(rows, spec, parse_numeric_strings=True) == []
    spec.entities[0].fields[0].data_type = FieldType.STRING
    assert safety.validate_generated_row_privacy(rows, spec, parse_numeric_strings=True) == [
        "generated dataset failed post-solve privacy validation"
    ]


def test_privacy_walk_matches_original_for_seeded_mixed_datasets():
    rng = random.Random(74109)
    values = _value_cases()
    for case_index in range(80):
        spec = _spec([
            _field(name="payload", data_type=rng.choice(list(FieldType)),
                      semantic_type=rng.choice([None, "email", "phone", "ssn", "identifier"]),
                      sensitive=rng.choice([False, True])),
            FieldSpec(name="quantity", data_type=FieldType.INTEGER),
            FieldSpec(name="contact_name", data_type=FieldType.STRING),
        ])
        spec.entities.append(spec.entities[0].model_copy(update={"name": "other"}, deep=True))
        rows = {
            entity.name: [
                {field.name: deepcopy(rng.choice(values)[1]) for field in entity.fields}
                for _ in range(rng.randrange(5))
            ]
            for entity in spec.entities
        }
        for parse in (False, True):
            _assert_equivalent(f"seeded_{case_index}", rows, spec, parse)


def test_privacy_walk_prepares_field_names_once_and_skips_only_actual_non_strings(monkeypatch):
    spec = _spec([
        FieldSpec(name="payload", data_type=FieldType.STRING),
        FieldSpec(name="quantity", data_type=FieldType.INTEGER),
        FieldSpec(name="enabled", data_type=FieldType.BOOLEAN),
        FieldSpec(name="day", data_type=FieldType.DATE),
    ])
    rows = {"records": [
        {"payload": "ordinary_category", "quantity": 1234567, "enabled": True, "day": date(2026, 1, 2)},
        {"payload": "synthetic_record", "quantity": 2, "enabled": False, "day": date(2026, 1, 3)},
        {"payload": 1234567, "quantity": "ordinary_category", "enabled": False, "day": None},
    ]}
    classify_name = Mock(wraps=safety.is_sensitive_field)
    classify_value = Mock(wraps=safety.infer_sensitive_value_type)
    monkeypatch.setattr(safety, "is_sensitive_field", classify_name)
    monkeypatch.setattr(safety, "infer_sensitive_value_type", classify_value)

    assert safety.validate_generated_row_privacy(rows, spec) == []

    assert classify_name.call_count == len(spec.entities[0].fields)
    assert classify_value.call_count == 3
    assert all(isinstance(call.args[0], str) for call in classify_value.call_args_list)
    rows["records"] = [{"quantity": "1234567"}]
    assert safety.validate_generated_row_privacy(rows, spec) == [
        "generated dataset failed post-solve privacy validation"
    ]
    assert classify_value.call_count == 4
    assert safety.validate_generated_row_privacy(rows, spec, parse_numeric_strings=True) == []
    assert classify_value.call_count == 4
