"""Constraint solving over synthetic rows."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from test_data_agent.business_validator import condition_matches, safe_eval
from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetSpec


def solve_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec, seed: int) -> None:
    apply_relationships(rows_by_entity, spec)
    apply_formula_constraints(rows_by_entity, spec)
    apply_temporal_constraints(rows_by_entity, spec)
    apply_conditional_required_constraints(rows_by_entity, spec)
    apply_aggregate_mapping_constraints(rows_by_entity, spec)


def apply_relationships(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for relationship in spec.relationships:
        parent_rows = rows_by_entity.get(relationship.parent_entity, [])
        child_rows = rows_by_entity.get(relationship.child_entity, [])
        parent_values = [row.get(relationship.parent_field) for row in parent_rows if row.get(relationship.parent_field) is not None]
        if not parent_values:
            continue
        for index, child_row in enumerate(child_rows):
            child_row[relationship.child_field] = parent_values[index % len(parent_values)]


def apply_formula_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.FORMULA or not constraint.expression or not constraint.fields:
            continue
        target = constraint.fields[0]
        for row in rows_by_entity.get(constraint.entity, []):
            row[target] = safe_eval(constraint.expression, row)


def apply_temporal_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.TEMPORAL or len(constraint.fields) < 2:
            continue
        start_field, end_field = constraint.fields[:2]
        for row in rows_by_entity.get(constraint.entity, []):
            start = parse_datetime(row.get(start_field))
            end = parse_datetime(row.get(end_field))
            if start is not None and (end is None or end < start):
                row[end_field] = row[start_field]


def apply_conditional_required_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.CONDITIONAL_REQUIRED or not constraint.condition:
            continue
        condition = SimpleCondition(**constraint.condition)
        for row in rows_by_entity.get(constraint.entity, []):
            if condition_matches(row, condition):
                for field in constraint.fields:
                    if row.get(field) in (None, ""):
                        row[field] = "required"


def apply_aggregate_mapping_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.AGGREGATE_MAPPING or not constraint.target_entity or not constraint.target_field:
            continue
        relationship = next(
            (
                item for item in spec.relationships
                if item.parent_entity == constraint.entity and item.child_entity == constraint.target_entity
            ),
            None,
        )
        if relationship is None:
            continue
        totals: dict[Any, float] = defaultdict(float)
        for child_row in rows_by_entity.get(relationship.child_entity, []):
            key = child_row.get(relationship.child_field)
            totals[key] += float(child_row.get(constraint.target_field) or 0.0)
        parent_field = constraint.fields[0] if constraint.fields else None
        if parent_field is None:
            continue
        for parent_row in rows_by_entity.get(relationship.parent_entity, []):
            key = parent_row.get(relationship.parent_field)
            parent_row[parent_field] = normalize_number(totals.get(key, 0.0))


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class SimpleCondition:
    def __init__(self, field: str, equals: Any | None = None, not_equals: Any | None = None, in_values: list[Any] | None = None):
        self.field = field
        self.equals = equals
        self.not_equals = not_equals
        self.in_values = in_values


def normalize_number(value: float) -> int | float:
    rounded = round(value, 6)
    return int(rounded) if float(rounded).is_integer() else rounded
