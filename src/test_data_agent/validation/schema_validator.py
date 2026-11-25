"""Schema validation for generated datasets."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import partial
import math
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.decimal_units import value_matches_decimal
from test_data_agent.core.distribution import DecimalRangeDistribution, StringPatternDistribution
from test_data_agent.core.field import FieldType
from test_data_agent.csv_profiler import parse_bool, parse_date_value, parse_datetime_value, parse_float, parse_int


def validate_schema(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> list[str]:
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
            errors.append(
                f"{entity.name} row count mismatch: expected {entity.row_count}, got {len(rows)}"
            )
        expected_fields = {field.name for field in entity.fields}
        field_checks = []
        for field in entity.fields:
            distribution = field.typed_distribution
            bounds = (
                (distribution.min_length, distribution.max_length)
                if isinstance(distribution, StringPatternDistribution) else None
            )
            checker = (_decimal_checker(distribution) if field.data_type == FieldType.DECIMAL
                       else _type_checker(field.data_type))
            field_checks.append((field.name, field.nullable, checker, bounds))
        primary_key = entity.primary_key
        primary_key_checker: Callable[[Any], bool] | None = None
        primary_key_values: set[Any] = set()
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{entity.name}[{row_index}] row must be an object")
                continue
            if set(row) != expected_fields:
                errors.append(f"{entity.name}[{row_index}] fields mismatch")
                continue
            if primary_key is not None:
                primary_key_value = row.get(primary_key)
                if primary_key_value in (None, ""):
                    errors.append(f"{entity.name}[{row_index}].{primary_key} is required")
                else:
                    if primary_key_checker is None:
                        key_field = entity.field(primary_key)
                        primary_key_checker = (_decimal_checker(key_field.typed_distribution)
                                               if key_field.data_type == FieldType.DECIMAL
                                               else _type_checker(key_field.data_type))
                    if not primary_key_checker(primary_key_value):
                        errors.append(f"{entity.name}[{row_index}].{primary_key} has wrong type")
                    elif primary_key_value in primary_key_values:
                        errors.append(f"{entity.name}[{row_index}].{primary_key} is not unique")
                    else:
                        primary_key_values.add(primary_key_value)
            for field_name, nullable, matches_type, bounds in field_checks:
                value = row.get(field_name)
                if value in (None, ""):
                    if not nullable:
                        errors.append(f"{entity.name}[{row_index}].{field_name} is required")
                    continue
                if (
                    isinstance(value, str)
                    and bounds is not None
                    and not bounds[0] <= len(value) <= bounds[1]
                ):
                    errors.append(f"{entity.name}[{row_index}].{field_name} has wrong length")
                if not matches_type(value):
                    errors.append(f"{entity.name}[{row_index}].{field_name} has wrong type")
    return errors


def value_matches_type(value: Any, data_type: FieldType) -> bool:
    return _type_checker(data_type)(value)


def _decimal_checker(distribution: Any) -> Callable[[Any], bool]:
    if not isinstance(distribution, DecimalRangeDistribution):
        return lambda value: False
    return partial(value_matches_decimal, precision=distribution.precision,
                   scale=distribution.scale, low=distribution.min, high=distribution.max)


def _type_checker(data_type: FieldType) -> Callable[[Any], bool]:
    if data_type == FieldType.INTEGER:
        return _matches_integer
    if data_type == FieldType.FLOAT:
        return _matches_float
    if data_type == FieldType.BOOLEAN:
        return _matches_boolean
    if data_type == FieldType.DATE:
        return _matches_date
    if data_type == FieldType.DATETIME:
        return _matches_datetime
    return _matches_string


def _matches_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) or parse_int(str(value)) is not None


def _matches_float(value: Any) -> bool:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return not isinstance(value, float) or math.isfinite(value)
    return parse_float(str(value)) is not None


def _matches_boolean(value: Any) -> bool:
    return isinstance(value, bool) or parse_bool(str(value)) is not None


def _matches_date(value: Any) -> bool:
    return parse_date_value(str(value)) is not None


def _matches_datetime(value: Any) -> bool:
    return parse_datetime_value(str(value)) is not None


def _matches_string(value: Any) -> bool:
    return isinstance(value, str)
