"""Validation for generated synthetic datasets."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.spec import DataType, GenerationSpec


class ValidationReport(BaseModel):
    valid: bool
    row_count: int
    expected_row_count: int
    error_count: int
    errors: list[str] = Field(default_factory=list)


def validate_rows(rows: Sequence[dict[str, Any]], spec: GenerationSpec) -> list[str]:
    return validate_rows_report(rows, spec).errors


def validate_rows_report(rows: Sequence[dict[str, Any]], spec: GenerationSpec) -> ValidationReport:
    errors: list[str] = []
    expected_names = [column.name for column in spec.table.columns]

    if len(rows) != spec.table.row_count:
        errors.append(f"expected {spec.table.row_count} rows, got {len(rows)}")

    for row_index, row in enumerate(rows):
        actual_names = list(row.keys())
        if actual_names != expected_names:
            errors.append(
                f"row {row_index} columns mismatch: expected {expected_names}, got {actual_names}"
            )
            continue

        for column in spec.table.columns:
            value = row[column.name]
            if value is None:
                if not column.nullable:
                    errors.append(f"row {row_index}.{column.name} is null but column is not nullable")
                continue
            if not value_matches_type(value, column.data_type):
                errors.append(
                    f"row {row_index}.{column.name} expected {column.data_type}, got {type(value).__name__}"
                )
                continue
            if column.choices is not None and value not in column.choices:
                errors.append(f"row {row_index}.{column.name} is not in allowed choices")
            if column.min_value is not None and isinstance(value, int | float) and value < column.min_value:
                errors.append(f"row {row_index}.{column.name} is below minimum")
            if column.max_value is not None and isinstance(value, int | float) and value > column.max_value:
                errors.append(f"row {row_index}.{column.name} is above maximum")
            if column.data_type == DataType.DATE and not date_in_range(value, column.min_date, column.max_date):
                errors.append(f"row {row_index}.{column.name} is outside date range")
            if column.data_type == DataType.DATETIME and not datetime_in_range(
                value, column.min_datetime, column.max_datetime
            ):
                errors.append(f"row {row_index}.{column.name} is outside datetime range")

    return ValidationReport(
        valid=not errors,
        row_count=len(rows),
        expected_row_count=spec.table.row_count,
        error_count=len(errors),
        errors=errors,
    )


def value_matches_type(value: Any, data_type: DataType) -> bool:
    if data_type == DataType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if data_type == DataType.FLOAT:
        return isinstance(value, int | float) and not isinstance(value, bool)
    if data_type == DataType.BOOLEAN:
        return isinstance(value, bool)
    if data_type == DataType.DATE:
        return parse_date_value(value) is not None
    if data_type == DataType.DATETIME:
        return parse_datetime_value(value) is not None
    return isinstance(value, str)


def date_in_range(value: Any, min_date: date | None, max_date: date | None) -> bool:
    parsed = parse_date_value(value)
    if parsed is None:
        return False
    if min_date is not None and parsed < min_date:
        return False
    if max_date is not None and parsed > max_date:
        return False
    return True


def datetime_in_range(value: Any, min_datetime: datetime | None, max_datetime: datetime | None) -> bool:
    parsed = parse_datetime_value(value)
    if parsed is None:
        return False
    if min_datetime is not None and parsed < min_datetime:
        return False
    if max_datetime is not None and parsed > max_datetime:
        return False
    return True


def parse_date_value(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_datetime_value(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
