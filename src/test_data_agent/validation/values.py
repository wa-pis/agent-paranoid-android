"""Non-mutating, schema-directed values for artifact validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.field import FieldType
from test_data_agent.csv_profiler import parse_bool, parse_float, parse_int


def normalize_dataset_values(
    rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Preserve input identity when no conversion or structural error occurs."""
    normalized: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    changed = False
    scalar_types = (str, int, float, bool, date, datetime, Decimal)
    parsers = {FieldType.INTEGER: parse_int, FieldType.FLOAT: parse_float, FieldType.BOOLEAN: parse_bool}
    entity_fields = {
        entity.name: {
            field.name: (parsers.get(field.data_type), field.nullable)
            for field in entity.fields
        }
        for entity in spec.entities
    }
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
                if value is not None and not isinstance(value, scalar_types):
                    errors.append(f"{name}[{index}].{field_name} must be a scalar")
                    continue
                if not isinstance(value, str):
                    continue
                parser, nullable = fields.get(field_name, (None, False))
                if parser is None:
                    continue
                empty_null = value == "" and nullable
                parsed = None if empty_null else parser(value)
                if parsed is not None or empty_null:
                    if converted is row:
                        converted = row.copy()
                        changed = True
                    converted[field_name] = parsed
            normalized_rows.append(converted)
        normalized[name] = normalized_rows
    return (normalized if changed or errors else rows_by_entity), errors
