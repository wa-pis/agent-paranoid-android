"""Freeze normalization decisions, diagnostics and copy-on-write behavior."""

from __future__ import annotations

import math
import random
from collections import UserDict
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.csv_profiler import parse_bool, parse_float, parse_int
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.validation.values import normalize_dataset_values


def _original_normalize(
    rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    # Frozen before optimization; never call the candidate's preparation helpers.
    normalized: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    changed = False
    entity_fields = {
        entity.name: {field.name: field for field in entity.fields}
        for entity in spec.entities
    }
    parsers = {FieldType.INTEGER: parse_int, FieldType.FLOAT: parse_float, FieldType.BOOLEAN: parse_bool}
    for name, rows in rows_by_entity.items():
        if not isinstance(rows, list):
            errors.append(f"{name} rows must be a list")
            continue
        normalized_rows: list[dict[str, Any]] = []
        fields = entity_fields.get(name, {})
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{name}[{index}] row must be an object")
                continue
            converted = row
            for field_name, value in row.items():
                if value is not None and not isinstance(value, (str, int, float, bool, date, datetime, Decimal)):
                    errors.append(f"{name}[{index}].{field_name} must be a scalar")
                    continue
                field = fields.get(field_name)
                parser = parsers.get(field.data_type) if field is not None else None
                if not isinstance(value, str) or parser is None:
                    continue
                empty_null = value == "" and field is not None and field.nullable
                parsed = None if empty_null else parser(value)
                if parsed is not None or empty_null:
                    if converted is row:
                        converted = row.copy()
                        changed = True
                    converted[field_name] = parsed
            normalized_rows.append(converted)
        normalized[name] = normalized_rows
    return (normalized if changed or errors else rows_by_entity), errors


class _IntegerSubclass(int):
    pass


class _FloatSubclass(float):
    pass


class _ListSubclass(list):
    pass


class _DictSubclass(dict):
    pass


class _StringSubclass(str):
    def __str__(self) -> str:
        return "synthetic_overridden_string"


class _EmptyEqualString(str):
    def __eq__(self, other: object) -> bool:
        return other == ""


class _RaisingLowerString(str):
    def lower(self) -> str:
        raise ValueError("synthetic lowercase failure")


class _RaisingCopyDict(dict):
    def copy(self):
        raise ValueError("synthetic copy failure")


class _RaisingItemsDict(dict):
    def items(self):
        raise ValueError("synthetic iteration failure")


class _ReverseItemsDict(dict):
    def items(self):
        return reversed(list(super().items()))


class _NoRepresentation:
    def __repr__(self) -> str:
        raise AssertionError("normalization must not format a value")


def _spec(data_type: FieldType = FieldType.STRING, *, nullable: bool = False) -> DatasetSpec:
    distribution = ({"kind": "decimal_range", "precision": 6, "scale": 2,
                     "min": "-9999.99", "max": "9999.99"}
                    if data_type == FieldType.DECIMAL else {})
    return DatasetSpec.model_validate({
        "schema_version": "1.1",
        "entities": [{"name": "records", "row_count": 3, "fields": [
            {"name": "payload", "data_type": data_type, "nullable": nullable,
             "distribution": distribution},
            {"name": "other", "data_type": "string", "nullable": True},
        ]}],
    })


def _values() -> list[Any]:
    return [
        None, "", " ", "\t", 0, 1, -7, 2**70, 10**5000, False, True,
        0.0, 1.5, -0.0, float("nan"), float("inf"), float("-inf"),
        _IntegerSubclass(7), _FloatSubclass(1.5), Decimal("7"), Decimal("NaN"),
        "0", "7", "-7", " 7 ", "+7", "007", "7.0", "7e0", "1_0", "١", "７",
        "nan", "Infinity", "true", "TRUE", "t", "yes", " false ", "no", "0x10",
        "2024-02-29", "2024-02-29T01:02:03Z", date(2024, 2, 29),
        datetime(2024, 2, 29, 1, 2, 3, tzinfo=timezone.utc),
        _StringSubclass("7"), _StringSubclass("true"), _EmptyEqualString("7"),
        _RaisingLowerString("true"), b"7", bytearray(b"7"), [], {}, (), {1},
        frozenset({1}), UserDict(payload=7), _NoRepresentation(),
    ]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return type(value), tuple((key, _canonical(item)) for key, item in dict.items(value))
    if isinstance(value, list):
        return type(value), tuple(_canonical(item) for item in value)
    if isinstance(value, str):
        return type(value), str.__str__(value)
    if isinstance(value, float) and math.isnan(value):
        return type(value), "synthetic_nan_marker"
    if isinstance(value, Decimal):
        return type(value), value.as_tuple()
    if isinstance(value, (type(None), bool, int, float, date, datetime, bytes, bytearray)):
        return type(value), value
    return type(value)


def _outcome(function, rows: dict[str, Any], spec: DatasetSpec) -> Any:
    original = _canonical(rows)
    try:
        normalized, errors = function(rows, spec)
    except Exception as error:
        assert _canonical(rows) == original
        return "exception", type(error), error.args
    assert _canonical(rows) == original
    identities = []
    for name, normalized_rows in normalized.items():
        original_rows = rows[name]
        originals = original_rows if isinstance(original_rows, list) else []
        identities.append((
            name, normalized_rows is original_rows,
            tuple(tuple(index for index, original_row in enumerate(originals) if row is original_row)
                  for row in normalized_rows),
        ))
    return _canonical(normalized), errors, normalized is rows, identities


def _assert_equivalent(rows: dict[str, Any], spec: DatasetSpec) -> None:
    assert _outcome(normalize_dataset_values, rows, spec) == _outcome(
        _original_normalize, rows, spec,
    )


@pytest.mark.parametrize("data_type", list(FieldType))
@pytest.mark.parametrize("nullable", [False, True])
def test_normalization_preserves_frozen_scalar_and_parser_policy(
    data_type: FieldType, nullable: bool,
) -> None:
    spec = _spec(data_type, nullable=nullable)
    for value in _values():
        _assert_equivalent({"records": [{"payload": value, "other": "synthetic_value"}]}, spec)


def test_normalization_preserves_exact_structural_errors_and_order() -> None:
    spec = _spec(FieldType.INTEGER)
    rows = {
        "records": [None, {"payload": [], "other": {}}, {"payload": "7", "unknown": ()}],
        "unknown": [{"payload": [], "extra": {}}, {"payload": "7"}],
        "not_a_list": (),
    }
    expected = [
        "records[0] row must be an object", "records[1].payload must be a scalar",
        "records[1].other must be a scalar", "records[2].unknown must be a scalar",
        "unknown[0].payload must be a scalar", "unknown[0].extra must be a scalar",
        "not_a_list rows must be a list",
    ]
    _assert_equivalent(rows, spec)
    normalized, errors = normalize_dataset_values(rows, spec)
    assert errors == expected
    assert list(normalized) == ["records", "unknown"]
    assert len(normalized["records"]) == 2
    assert normalized["records"][0] is rows["records"][1]
    assert normalized["records"][1] is not rows["records"][2]
    assert normalized["records"][1]["payload"] == 7


def test_normalization_is_copy_on_write_without_changing_aliases_or_inputs() -> None:
    spec = _spec(FieldType.INTEGER, nullable=True)
    shared = {"payload": "7", "other": "synthetic_value"}
    untouched = {"payload": 8, "other": "synthetic_other"}
    rows = {"records": [shared, untouched, shared], "unknown": [shared]}
    original = deepcopy(rows)
    normalized, errors = normalize_dataset_values(rows, spec)
    assert not errors and rows == original
    assert normalized is not rows
    assert normalized["records"] is not rows["records"]
    assert normalized["unknown"] is not rows["unknown"]
    assert normalized["records"][0] is not shared
    assert normalized["records"][2] is not shared
    assert normalized["records"][0] is not normalized["records"][2]
    assert normalized["records"][1] is untouched
    assert normalized["unknown"][0] is shared
    _assert_equivalent(rows, spec)


def test_native_or_unconvertible_values_retain_the_complete_input_identity() -> None:
    spec = _spec(FieldType.INTEGER, nullable=False)
    for value in (None, 7, False, date(2024, 2, 29), "", "007", "synthetic_text"):
        row = {"payload": value}
        rows = {"records": [row], "unknown": [{"payload": "7"}], "empty": []}
        normalized, errors = normalize_dataset_values(rows, spec)
        assert not errors and normalized is rows
        assert normalized["records"][0] is row
    for field_type in (FieldType.STRING, FieldType.DATE, FieldType.DATETIME):
        rows = {"records": [{"payload": ""}]}
        assert normalize_dataset_values(rows, _spec(field_type, nullable=True)) == (rows, [])
        assert normalize_dataset_values(rows, _spec(field_type, nullable=True))[0] is rows


def test_errors_alone_rebuild_containers_but_keep_unchanged_rows() -> None:
    spec = _spec()
    row = {"payload": "synthetic_value", "unknown": []}
    rows = {"records": [None, row], "empty": []}
    normalized, errors = normalize_dataset_values(rows, spec)
    assert errors == ["records[0] row must be an object", "records[1].unknown must be a scalar"]
    assert normalized is not rows and normalized["records"] is not rows["records"]
    assert normalized["records"] == [row] and normalized["records"][0] is row
    assert normalized["empty"] is not rows["empty"]
    _assert_equivalent(rows, spec)


def test_normalization_keeps_list_dict_and_string_subclass_behavior() -> None:
    spec = _spec(FieldType.INTEGER, nullable=True)
    for row in (
        _DictSubclass(payload="7"), _DictSubclass(payload=7),
        _RaisingCopyDict(payload="7"), _RaisingCopyDict(payload=7),
        _RaisingItemsDict(payload="7"), _ReverseItemsDict(payload=[], other={}),
        UserDict(payload="7"), MappingProxyType({"payload": "7"}),
    ):
        if isinstance(row, MappingProxyType):
            for function in (_original_normalize, normalize_dataset_values):
                result, errors = function({"records": [row]}, spec)
                assert result == {"records": []} and errors == ["records[0] row must be an object"]
        else:
            _assert_equivalent({"records": _ListSubclass([row])}, spec)
    for value in (_StringSubclass("7"), _EmptyEqualString("7")):
        _assert_equivalent({"records": [{"payload": value}]}, spec)


def test_normalization_reads_fresh_specifications_and_rows_on_every_call() -> None:
    spec = _spec(FieldType.INTEGER)
    rows = {"records": [{"payload": "7", "other": "synthetic_value"}]}
    for field_type in FieldType:
        spec.entities[0].fields[0] = _spec(field_type).entities[0].fields[0]
        _assert_equivalent(rows, spec)
    field = _spec(FieldType.INTEGER).entities[0].fields[0]
    spec.entities[0].fields[0] = field
    for nullable in (False, True, False):
        field.nullable = nullable
        rows["records"][0]["payload"] = ""
        _assert_equivalent(rows, spec)
    field.name = "renamed"
    _assert_equivalent(rows, spec)
    rows["records"][0]["renamed"] = "7"
    _assert_equivalent(rows, spec)
    spec.entities[0].fields.append(FieldSpec(name="added", data_type="boolean"))
    rows["records"][0]["added"] = "true"
    _assert_equivalent(rows, spec)


def test_mutated_duplicate_fields_keep_last_field_even_when_it_has_no_parser() -> None:
    spec = _spec(FieldType.INTEGER, nullable=True)
    last = FieldSpec(name="payload", data_type="string", nullable=True)
    spec.entities[0].fields.append(last)
    for value in ("7", "", "true"):
        rows = {"records": [{"payload": value}]}
        _assert_equivalent(rows, spec)
        assert normalize_dataset_values(rows, spec)[0] is rows
    last.data_type = FieldType.BOOLEAN
    _assert_equivalent({"records": [{"payload": "true"}]}, spec)
    last.data_type = FieldType.INTEGER
    _assert_equivalent({"records": [{"payload": "7"}]}, spec)


def test_normalization_matches_frozen_policy_for_seeded_mixed_datasets() -> None:
    rng = random.Random(1123)
    values = _values()
    for _ in range(100):
        spec = _spec(rng.choice(list(FieldType)), nullable=rng.choice([True, False]))
        rows = {"records": [
            {"payload": rng.choice(values), "other": rng.choice(values), "unknown": rng.choice(values)}
            for _ in range(rng.randrange(5))
        ], "unknown": [{"payload": rng.choice(values)}]}
        _assert_equivalent(rows, spec)


@pytest.mark.parametrize("source_type", [
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile", "postgres",
    "postgres_query", "trino", "trino_query", "custom_source",
])
def test_source_inferred_specs_share_normalization_policy(source_type: str) -> None:
    profile = DatasetProfile.model_validate({
        "source_type": source_type,
        "has_unmodeled_expressions": False,
        "entities": [{"name": "records", "row_count": 1, "fields": [
            {"name": data_type.value, "data_type": data_type,
             **({"decimal_precision": 6, "decimal_scale": 2}
                if data_type == FieldType.DECIMAL else {})} for data_type in FieldType
        ]}],
    })
    reviewed = _spec(FieldType.DECIMAL).entities[0].fields[0]
    reviewed.name = "decimal"
    spec = infer_dataset_spec(profile, count=1, decimal_fields={"records.decimal": reviewed})
    assert {field.data_type for field in spec.entities[0].fields} == set(FieldType)
    row = {"integer": "7", "float": "1.5", "decimal": "7.25",
           "boolean": "true", "string": "synthetic_value",
           "date": "2024-02-29", "datetime": "2024-02-29T01:02:03Z"}
    rows = {"records": [row]}
    _assert_equivalent(rows, spec)
    normalized, errors = normalize_dataset_values(rows, spec)
    assert not errors
    assert normalized["records"][0] == {**row, "integer": 7, "float": 1.5, "boolean": True}
    _assert_equivalent({"records": [{name: [] for name in row}]}, spec)
