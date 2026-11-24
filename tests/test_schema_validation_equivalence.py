"""Preserve the pre-optimization schema policy, including error order."""

from __future__ import annotations

import math
import random
from collections import UserDict
from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Callable

import pytest
from pydantic import ValidationError

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.decimal_units import value_matches_decimal
from test_data_agent.core.distribution import DecimalRangeDistribution, StringPatternDistribution
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.csv_profiler import (
    parse_bool,
    parse_date_value,
    parse_datetime_value,
    parse_float,
    parse_int,
)
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.validation.schema_validator import validate_schema, value_matches_type


def _original_type_match(value: Any, data_type: FieldType) -> bool:
    if data_type == FieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool) or parse_int(str(value)) is not None
    if data_type == FieldType.FLOAT:
        if type(value) is int:
            return True
        if isinstance(value, str):
            value = parse_float(value)
        return isinstance(value, float) and math.isfinite(value)
    if data_type == FieldType.BOOLEAN:
        return isinstance(value, bool) or parse_bool(str(value)) is not None
    if data_type == FieldType.DATE:
        return parse_date_value(str(value)) is not None
    if data_type == FieldType.DATETIME:
        return parse_datetime_value(str(value)) is not None
    return isinstance(value, str)


def _original_field_match(value: Any, field: FieldSpec) -> bool:
    if field.data_type == FieldType.DECIMAL:
        distribution = field.typed_distribution
        return isinstance(distribution, DecimalRangeDistribution) and value_matches_decimal(
            value, precision=distribution.precision, scale=distribution.scale,
            low=distribution.min, high=distribution.max,
        )
    return _original_type_match(value, field.data_type)


def _original_schema(rows_by_entity: dict[str, list[Any]], spec: DatasetSpec) -> list[str]:
    # Freeze the complete original walk rather than calling candidate helpers.
    errors: list[str] = []
    expected_entity_names = {entity.name for entity in spec.entities}
    unexpected_entity_names = sorted(set(rows_by_entity) - expected_entity_names)
    for entity_name in unexpected_entity_names:
        errors.append(f"unexpected entity: {entity_name}")
    for entity in spec.entities:
        rows = rows_by_entity.get(entity.name)
        if rows is None:
            errors.append(f"missing entity: {entity.name}")
            continue
        if len(rows) != entity.row_count:
            errors.append(f"{entity.name} row count mismatch: expected {entity.row_count}, got {len(rows)}")
        expected_fields = {field.name for field in entity.fields}
        distributions = [(field, field.typed_distribution) for field in entity.fields]
        primary_key_values: set[Any] = set()
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{entity.name}[{row_index}] row must be an object")
                continue
            if set(row) != expected_fields:
                errors.append(f"{entity.name}[{row_index}] fields mismatch")
                continue
            if entity.primary_key is not None:
                value = row.get(entity.primary_key)
                if value in (None, ""):
                    errors.append(f"{entity.name}[{row_index}].{entity.primary_key} is required")
                elif not _original_field_match(value, entity.field(entity.primary_key)):
                    errors.append(f"{entity.name}[{row_index}].{entity.primary_key} has wrong type")
                elif value in primary_key_values:
                    errors.append(f"{entity.name}[{row_index}].{entity.primary_key} is not unique")
                else:
                    primary_key_values.add(value)
            for field, distribution in distributions:
                value = row.get(field.name)
                if value in (None, ""):
                    if not field.nullable:
                        errors.append(f"{entity.name}[{row_index}].{field.name} is required")
                    continue
                if (
                    isinstance(value, str)
                    and isinstance(distribution, StringPatternDistribution)
                    and not distribution.min_length <= len(value) <= distribution.max_length
                ):
                    errors.append(f"{entity.name}[{row_index}].{field.name} has wrong length")
                if not _original_field_match(value, field):
                    errors.append(f"{entity.name}[{row_index}].{field.name} has wrong type")
    return errors


class _IntegerSubclass(int):
    pass


class _FloatSubclass(float):
    pass


class _DateSubclass(date):
    def __str__(self) -> str:
        return "synthetic_not_a_date"


class _DatetimeSubclass(datetime):
    def __str__(self) -> str:
        return "synthetic_not_a_datetime"


class _StringSubclass(str):
    def __str__(self) -> str:
        return "7"


class _StringScalar:
    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


class _RaisingScalar:
    def __str__(self) -> str:
        raise ValueError("synthetic conversion failure")


class _DuplicateKeyMapping(Mapping[str, Any]):
    def __iter__(self):
        return iter(["payload", "payload"])

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str) -> Any:
        if key != "payload":
            raise KeyError(key)
        return "synthetic_value"


def _values() -> list[Any]:
    return [
        None, "", " ", "\t", False, True, 0, 1, -7, 2**70, 10**5000,
        _IntegerSubclass(7), 0.0, 1.5, -0.0, float("nan"), float("inf"), float("-inf"),
        _FloatSubclass(1.5), Decimal("7"), Decimal("1.5"), Decimal("NaN"),
        Decimal("7.00"), Decimal("1.234"), Decimal("9999.99"), Decimal("10000.00"),
        Decimal("-9999.99"), Decimal("Infinity"), "7.01", "1.234", "9999.99", "10000.00",
        "0", "7", "-7", " 7 ", "+7", "007", "7.0", "7e0", "١", "７", "1_0",
        "nan", "Infinity", "true", "TRUE", "t", "yes", " false ", "no", "0x10",
        "2024-02-29", "2024-02-30", "20240229", "2024-W09-4", "2024-02-29suffix",
        " 2024-02-29", "2024-02-29T01:02:03Z", "2024-02-29 01:02:03 +0000",
        "2024-02-29T01:02:03+02:30", "2024-02-29T25:00:00", "2024-02-29\t01:02:03",
        date(2024, 2, 29), datetime(2024, 2, 29, 1, 2, 3),
        datetime(2024, 2, 29, tzinfo=timezone.utc),
        _DateSubclass(2024, 2, 29), _DatetimeSubclass(2024, 2, 29),
        _StringSubclass("synthetic_text"), _StringScalar("7"),
        _StringScalar("2024-02-29"), _StringScalar("2024-02-29T01:02:03Z"),
        _StringScalar("true"), _RaisingScalar(), b"7", [], {}, (), {1}, frozenset({1}),
    ]


def _outcome(function: Callable[[], Any]) -> Any:
    try:
        return function()
    except Exception as error:
        return type(error), error.args


def _assert_equivalent(rows: dict[str, list[Any]], spec: DatasetSpec) -> None:
    assert _outcome(lambda: validate_schema(rows, spec)) == _outcome(lambda: _original_schema(rows, spec))


def _field(data_type: FieldType, *, name: str = "payload", nullable: bool = False,
           is_identifier: bool = False) -> FieldSpec:
    distribution = ({"kind": "decimal_range", "precision": 6, "scale": 2,
                     "min": "-9999.99", "max": "9999.99"}
                    if data_type == FieldType.DECIMAL else {})
    return FieldSpec(name=name, data_type=data_type, nullable=nullable,
                     is_identifier=is_identifier, distribution=distribution)


def _spec(data_type: FieldType = FieldType.STRING, *, primary_key: bool = False) -> DatasetSpec:
    return DatasetSpec.model_validate({
        "schema_version": "1.1",
        "entities": [{"name": "records", "row_count": 3,
                      "primary_key": "payload" if primary_key else None,
                      "fields": [_field(data_type, is_identifier=primary_key)]}],
    })


@pytest.mark.parametrize("data_type", list(FieldType))
def test_type_dispatch_matches_frozen_policy(data_type: FieldType) -> None:
    for index, value in enumerate(_values()):
        assert _outcome(lambda: value_matches_type(value, data_type)) == _outcome(
            lambda: _original_type_match(value, data_type)
        ), index


@pytest.mark.parametrize("data_type", list(FieldType))
@pytest.mark.parametrize("primary_key", [False, True])
def test_schema_matches_frozen_value_nullable_length_and_key_policy(
    data_type: FieldType, primary_key: bool,
) -> None:
    if data_type == FieldType.DECIMAL and primary_key:
        with pytest.raises(ValidationError, match="decimal identifiers are not supported"):
            _spec(data_type, primary_key=True)
        return
    spec = _spec(data_type, primary_key=primary_key)
    field = spec.entities[0].fields[0]
    for nullable in (False, True):
        field.nullable = nullable
        distributions = (
            ({"kind": "decimal_range", "precision": 6, "scale": 2,
              "min": "-9999.99", "max": "9999.99"},
             {"kind": "decimal_range", "precision": 6, "scale": 2,
              "min": "7.01", "max": "8.00"})
            if data_type == FieldType.DECIMAL else
            ({}, {"kind": "string_pattern", "min_length": 2, "max_length": 4})
        )
        for distribution in distributions:
            field.distribution = distribution
            for value in _values():
                _assert_equivalent({"records": [{"payload": value}] * 3}, spec)


def test_decimal_primary_key_without_identifier_is_rejected() -> None:
    payload = _spec(FieldType.DECIMAL).model_dump(mode="json")
    payload["entities"][0]["primary_key"] = "payload"
    with pytest.raises(ValidationError, match="primary key must be an identifier field"):
        DatasetSpec.model_validate(payload)


def test_schema_preserves_entity_row_shape_and_error_order() -> None:
    spec = _spec(FieldType.INTEGER, primary_key=True)
    spec.entities[0].fields.append(FieldSpec(name="code", data_type=FieldType.INTEGER,
                                           distribution={"kind": "string_pattern", "min_length": 2,
                                                         "max_length": 4}))
    spec.entities.append(spec.entities[0].model_copy(update={"name": "later"}, deep=True))
    rows = {"z_extra": [], "a_extra": [], "records": [
        None, {"payload": None}, {"payload": None, "code": "not_integer"},
        {"payload": "bad", "code": "x"}, {"payload": 7, "code": 7},
        {"payload": 7, "code": "long_value"},
    ]}
    expected = [
        "unexpected entity: a_extra", "unexpected entity: z_extra",
        "records row count mismatch: expected 3, got 6", "records[0] row must be an object",
        "records[1] fields mismatch", "records[2].payload is required",
        "records[2].payload is required", "records[2].code has wrong length",
        "records[2].code has wrong type", "records[3].payload has wrong type",
        "records[3].payload has wrong type", "records[3].code has wrong length",
        "records[3].code has wrong type", "records[5].payload is not unique",
        "records[5].code has wrong length", "records[5].code has wrong type", "missing entity: later",
    ]
    assert _original_schema(rows, spec) == expected
    assert validate_schema(rows, spec) == expected
    for malformed in (None, "synthetic_row", 0, [], (), date(2024, 2, 29)):
        _assert_equivalent({"records": [malformed]}, spec)
    _assert_equivalent({}, spec)
    _assert_equivalent({"records": []}, spec)


def test_schema_keeps_non_dict_mappings_and_field_membership_policy() -> None:
    spec = _spec()
    for row in (UserDict(payload="synthetic_value"), MappingProxyType({"payload": "synthetic_value"}),
                _DuplicateKeyMapping(), {"payload": "synthetic_value", "extra": 1}, {}):
        _assert_equivalent({"records": [row]}, spec)
    spec.entities[0].fields = []
    _assert_equivalent({"records": [{}, UserDict(), MappingProxyType({})]}, spec)


def test_schema_preparation_observes_spec_and_row_mutations_between_calls() -> None:
    spec = _spec()
    spec.entities[0].row_count = 1
    rows = {"records": [{"payload": "7"}]}
    field = spec.entities[0].fields[0]
    for nullable, data_type, distribution in (
        (False, FieldType.STRING, {}),
        (False, FieldType.STRING, {"kind": "string_pattern", "min_length": 2, "max_length": 4}),
        (False, FieldType.INTEGER, {}), (True, FieldType.INTEGER, {}),
        (False, FieldType.DATE, {}),
    ):
        field.nullable, field.data_type, field.distribution = nullable, data_type, distribution
        _assert_equivalent(rows, spec)
    rows["records"][0]["payload"] = None
    _assert_equivalent(rows, spec)
    field.nullable = True
    _assert_equivalent(rows, spec)
    field.is_identifier = True
    spec.entities[0].primary_key = "payload"
    _assert_equivalent(rows, spec)
    field.data_type = FieldType.INTEGER
    rows["records"][0]["payload"] = "7"
    _assert_equivalent(rows, spec)
    before_rows, before_spec = deepcopy(rows), spec.model_dump(mode="json")
    validate_schema(rows, spec)
    assert rows == before_rows
    assert spec.model_dump(mode="json") == before_spec


def test_schema_preserves_lazy_lookup_for_mutated_missing_primary_key_field() -> None:
    spec = _spec(primary_key=True)
    spec.entities[0].fields.clear()
    for rows in ([], [None], [{"extra": 7}], [{}]):
        _assert_equivalent({"records": rows}, spec)
    rows = {"records": [{"payload": 7}]}
    _assert_equivalent(rows, spec)
    assert validate_schema(rows, spec)[-1] == "records[0] fields mismatch"

    class _KeyOutsideIteration(Mapping[str, Any]):
        def __iter__(self):
            return iter(())

        def __len__(self) -> int:
            return 0

        def __getitem__(self, key: str) -> Any:
            if key != "payload":
                raise KeyError(key)
            return 7

    rows = {"records": [_KeyOutsideIteration()]}
    assert _outcome(lambda: _original_schema(rows, spec)) == (KeyError, ("payload",))
    _assert_equivalent(rows, spec)


def test_schema_matches_frozen_policy_on_seeded_mixed_datasets() -> None:
    rng = random.Random(1123)
    values = _values()
    for _ in range(100):
        data_type = rng.choice(list(FieldType))
        primary_key = rng.choice([False, True]) and data_type != FieldType.DECIMAL
        spec = _spec(data_type, primary_key=primary_key)
        spec.entities[0].fields.extend([
            _field(rng.choice(list(FieldType)), name="other", nullable=rng.choice([False, True])),
            FieldSpec(name="text", data_type=FieldType.STRING,
                      distribution={"kind": "string_pattern", "min_length": 2, "max_length": 4}),
        ])
        spec.entities.append(spec.entities[0].model_copy(update={"name": "later"}, deep=True))
        rows = {entity.name: [
            {field.name: rng.choice(values) for field in entity.fields} for _ in range(rng.randrange(5))
        ] for entity in spec.entities}
        _assert_equivalent(rows, spec)


@pytest.mark.parametrize("source_type", [
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile", "postgres",
    "postgres_query", "trino", "trino_query", "custom_source",
])
def test_inferred_source_specs_share_schema_policy(source_type: str) -> None:
    profile = DatasetProfile.model_validate({
        "source_type": source_type,
        "has_unmodeled_expressions": False,
        "entities": [{"name": "records", "row_count": 1, "fields": [
            {"name": data_type.value, "data_type": data_type,
             **({"decimal_precision": 6, "decimal_scale": 2}
                if data_type == FieldType.DECIMAL else {})} for data_type in FieldType
        ]}],
    })
    with pytest.raises(ValueError, match="supply reviewed synthetic fields"):
        infer_dataset_spec(profile, count=1)
    spec = infer_dataset_spec(profile, count=1, decimal_fields={
        "records.decimal": _field(FieldType.DECIMAL, name="decimal"),
    })
    assert spec.schema_version == "1.1"
    assert {field.data_type for field in spec.entities[0].fields} == set(FieldType)
    valid = {"integer": 7, "float": 7.5, "decimal": Decimal("7.25"),
             "boolean": True, "string": "synthetic_value",
             "date": date(2024, 2, 29), "datetime": datetime(2024, 2, 29, 1, 2, 3)}
    assert validate_schema({"records": [valid]}, spec) == []
    invalid = {name: [] for name in valid}
    _assert_equivalent({"records": [invalid]}, spec)
    assert len(validate_schema({"records": [invalid]}, spec)) == len(FieldType)
