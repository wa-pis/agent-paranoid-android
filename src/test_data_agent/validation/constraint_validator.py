"""Constraint validation for generated datasets."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from test_data_agent.business_validator import condition_matches, safe_eval
from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.constraint_solver import SimpleCondition


def validate_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> list[str]:
    errors: list[str] = []
    for constraint in spec.constraints:
        if constraint.type == ConstraintType.FORMULA:
            errors.extend(validate_formula(rows_by_entity, constraint))
        elif constraint.type == ConstraintType.TEMPORAL:
            errors.extend(validate_temporal(rows_by_entity, constraint))
        elif constraint.type == ConstraintType.CONDITIONAL_REQUIRED:
            errors.extend(validate_conditional_required(rows_by_entity, constraint))
        elif constraint.type == ConstraintType.AGGREGATE_MAPPING:
            errors.extend(validate_aggregate_mapping(rows_by_entity, spec, constraint))
    return errors


def validate_formula(rows_by_entity: dict[str, list[dict[str, Any]]], constraint: Any) -> list[str]:
    if not constraint.expression or not constraint.fields:
        return []
    target = constraint.fields[0]
    errors: list[str] = []
    for index, row in enumerate(rows_by_entity.get(constraint.entity, [])):
        expected = safe_eval(constraint.expression, coerce_numeric_row(row))
        actual = row.get(target)
        if not numbers_close(actual, expected):
            errors.append(f"{constraint.entity}[{index}].{target} formula mismatch")
    return errors


def validate_temporal(rows_by_entity: dict[str, list[dict[str, Any]]], constraint: Any) -> list[str]:
    if len(constraint.fields) < 2:
        return []
    start_field, end_field = constraint.fields[:2]
    errors: list[str] = []
    for index, row in enumerate(rows_by_entity.get(constraint.entity, [])):
        start = parse_datetime(row.get(start_field))
        end = parse_datetime(row.get(end_field))
        if start is None or end is None or start > end:
            errors.append(f"{constraint.entity}[{index}] temporal ordering failed")
    return errors


def validate_conditional_required(rows_by_entity: dict[str, list[dict[str, Any]]], constraint: Any) -> list[str]:
    if not constraint.condition:
        return []
    condition = SimpleCondition(**constraint.condition)
    errors: list[str] = []
    for index, row in enumerate(rows_by_entity.get(constraint.entity, [])):
        if not condition_matches(row, condition):
            continue
        missing = [field for field in constraint.fields if row.get(field) in (None, "")]
        if missing:
            errors.append(f"{constraint.entity}[{index}] missing conditional fields {missing}")
    return errors


def validate_aggregate_mapping(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec, constraint: Any) -> list[str]:
    relationship = next(
        (
            item for item in spec.relationships
            if item.parent_entity == constraint.entity and item.child_entity == constraint.target_entity
        ),
        None,
    )
    if relationship is None or not constraint.target_field or not constraint.fields:
        return []
    totals: dict[Any, float] = defaultdict(float)
    for child_row in rows_by_entity.get(relationship.child_entity, []):
        totals[child_row.get(relationship.child_field)] += float(child_row.get(constraint.target_field) or 0.0)
    parent_field = constraint.fields[0]
    errors: list[str] = []
    for index, parent_row in enumerate(rows_by_entity.get(relationship.parent_entity, [])):
        key = parent_row.get(relationship.parent_field)
        if not numbers_close(parent_row.get(parent_field), totals.get(key, 0.0)):
            errors.append(f"{relationship.parent_entity}[{index}].{parent_field} aggregate mismatch")
    return errors


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def numbers_close(actual: Any, expected: Any, tolerance: float = 0.000001) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


def coerce_numeric_row(row: dict[str, Any]) -> dict[str, Any]:
    coerced: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, str):
            try:
                number = float(value)
            except ValueError:
                coerced[key] = value
                continue
            coerced[key] = int(number) if number.is_integer() else number
        else:
            coerced[key] = value
    return coerced
