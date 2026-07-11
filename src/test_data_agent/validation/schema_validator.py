"""Schema validation for generated datasets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
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
        expected_fields = [field.name for field in entity.fields]
        primary_key_values: set[Any] = set()
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{entity.name}[{row_index}] row must be an object")
                continue
            if list(row.keys()) != expected_fields:
                errors.append(f"{entity.name}[{row_index}] fields mismatch")
                continue
            if entity.primary_key is not None:
                primary_key_value = row.get(entity.primary_key)
                if primary_key_value in (None, ""):
                    errors.append(f"{entity.name}[{row_index}].{entity.primary_key} is required")
                elif primary_key_value in primary_key_values:
                    errors.append(f"{entity.name}[{row_index}].{entity.primary_key} is not unique")
                else:
                    primary_key_values.add(primary_key_value)
            for field in entity.fields:
                value = row.get(field.name)
                if value in (None, ""):
                    if not field.nullable and not field.is_identifier:
                        errors.append(f"{entity.name}[{row_index}].{field.name} is required")
                    continue
                if not value_matches_type(value, field.data_type):
                    errors.append(f"{entity.name}[{row_index}].{field.name} has wrong type")
    return errors


def value_matches_type(value: Any, data_type: FieldType) -> bool:
    if data_type == FieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool) or parse_int(str(value)) is not None
    if data_type == FieldType.FLOAT:
        return isinstance(value, int | float) and not isinstance(value, bool) or parse_float(str(value)) is not None
    if data_type == FieldType.BOOLEAN:
        return isinstance(value, bool) or parse_bool(str(value)) is not None
    if data_type == FieldType.DATE:
        return parse_date_value(str(value)) is not None
    if data_type == FieldType.DATETIME:
        return parse_datetime_value(str(value)) is not None
    return isinstance(value, str)
