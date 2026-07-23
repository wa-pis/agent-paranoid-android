"""Constraint solving over synthetic rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.distribution import (
    CategoricalDistribution,
    NumericDistribution,
    DateRangeDistribution,
    DateTimeRangeDistribution,
)
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.core.settings import GenerationMode
from test_data_agent.rules.conditions import Condition, condition_matches
from test_data_agent.rules.expressions import parse_datetime, safe_eval


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
        if relationship.relationship_type == RelationshipType.ONE_TO_ONE and len(child_rows) > len(parent_values):
            raise ValueError(
                f"one_to_one relationship has more child rows than parent rows: "
                f"{relationship.parent_entity}->{relationship.child_entity}"
            )
        for index, child_row in enumerate(child_rows):
            if relationship.relationship_type == RelationshipType.ONE_TO_ONE:
                child_row[relationship.child_field] = parent_values[index]
            else:
                child_row[relationship.child_field] = parent_values[index % len(parent_values)]


def apply_formula_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    allow_invalid_values = spec.generation_settings.mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.FORMULA or not constraint.expression or not constraint.fields:
            continue
        target = constraint.fields[0]
        for row in rows_by_entity.get(constraint.entity, []):
            try:
                row[target] = safe_eval(constraint.expression, row)
            except Exception as exc:
                if allow_invalid_values:
                    continue
                raise ValueError(
                    f"{constraint.entity}.{target} formula failed: {exc}"
                ) from exc


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
        condition = Condition(**constraint.condition)
        for row in rows_by_entity.get(constraint.entity, []):
            if condition_matches(row, condition):
                for field in constraint.fields:
                    if row.get(field) in (None, ""):
                        row[field] = default_value_for_field(spec.entity(constraint.entity).field(field))


def apply_aggregate_mapping_constraints(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> None:
    for constraint in spec.constraints:
        if constraint.type != ConstraintType.AGGREGATE_MAPPING or not constraint.target_entity:
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
        target_field = constraint.target_field
        for child_row in rows_by_entity.get(relationship.child_entity, []):
            key = child_row.get(relationship.child_field)
            if constraint.aggregate == "count":
                totals[key] += 1
                continue
            if target_field is None:
                continue
            try:
                totals[key] += float(child_row.get(target_field) or 0.0)
            except (TypeError, ValueError):
                continue
        parent_field = constraint.fields[0] if constraint.fields else None
        if parent_field is None:
            continue
        for parent_row in rows_by_entity.get(relationship.parent_entity, []):
            key = parent_row.get(relationship.parent_field)
            parent_row[parent_field] = normalize_number(totals.get(key, 0.0))

def normalize_number(value: float) -> int | float:
    rounded = round(value, 6)
    return int(rounded) if float(rounded).is_integer() else rounded


def default_value_for_field(field: FieldSpec) -> Any:
    distribution = field.typed_distribution
    if isinstance(distribution, CategoricalDistribution) and distribution.categories:
        return distribution.categories[0].value
    if isinstance(distribution, NumericDistribution):
        return next(
            (
                value
                for value in (
                    distribution.min_value,
                    distribution.p05,
                    distribution.max_value,
                    distribution.p95,
                )
                if value is not None
            ),
            0,
        )
    if isinstance(distribution, DateRangeDistribution):
        return distribution.min or "2000-01-01"
    if isinstance(distribution, DateTimeRangeDistribution):
        return distribution.min or "2000-01-01T00:00:00"
    if field.data_type == FieldType.INTEGER:
        return 0
    if field.data_type == FieldType.FLOAT:
        return 0.0
    if field.data_type == FieldType.BOOLEAN:
        return False
    if field.data_type == FieldType.DATE:
        return "2000-01-01"
    if field.data_type == FieldType.DATETIME:
        return "2000-01-01T00:00:00"
    if field.semantic_type == "email":
        return "synthetic@example.test"
    if field.semantic_type == "phone":
        return "+1-202-555-0100"
    return "required"
