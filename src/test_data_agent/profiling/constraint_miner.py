"""Heuristic constraint mining from example tables."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any

from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.field import FieldType
from test_data_agent.csv_profiler import parse_datetime_value, parse_float

MIN_CONFIDENCE = 0.9


def infer_constraints(profile: DatasetProfile, rows_by_entity: dict[str, list[dict[str, str]]]) -> list[Constraint]:
    constraints: list[Constraint] = []
    for entity in profile.entities:
        rows = rows_by_entity.get(entity.name, [])
        constraints.extend(infer_formula_constraints(entity.name, rows, numeric_fields(entity)))
        constraints.extend(infer_temporal_constraints(entity.name, rows, temporal_fields(entity)))
        constraints.extend(infer_conditional_required_constraints(entity.name, rows, entity.fields))
    constraints.extend(infer_aggregate_mapping_constraints(profile))
    return constraints


def numeric_fields(entity: Any) -> list[str]:
    return [field.name for field in entity.fields if field.data_type in {FieldType.INTEGER, FieldType.FLOAT} and not field.is_identifier]


def temporal_fields(entity: Any) -> list[str]:
    return [field.name for field in entity.fields if field.data_type in {FieldType.DATE, FieldType.DATETIME}]


def infer_formula_constraints(entity: str, rows: list[dict[str, str]], fields: list[str]) -> list[Constraint]:
    constraints: list[Constraint] = []
    for target in fields:
        sources = [field for field in fields if field != target]
        for left, right in combinations(sources, 2):
            for op, symbol in [(lambda a, b: a * b, "*"), (lambda a, b: a + b, "+")]:
                confidence = formula_confidence(rows, target, left, right, op)
                if confidence >= MIN_CONFIDENCE:
                    constraints.append(
                        Constraint(
                            type=ConstraintType.FORMULA,
                            entity=entity,
                            fields=[target, left, right],
                            expression=f"{left} {symbol} {right}",
                            confidence=round(confidence, 6),
                        )
                    )
                    return constraints
    return constraints


def formula_confidence(rows: list[dict[str, str]], target: str, left: str, right: str, op: Any) -> float:
    checked = 0
    matched = 0
    for row in rows:
        target_value = parse_float(row.get(target, ""))
        left_value = parse_float(row.get(left, ""))
        right_value = parse_float(row.get(right, ""))
        if target_value is None or left_value is None or right_value is None:
            continue
        checked += 1
        if abs(target_value - op(left_value, right_value)) <= 0.000001:
            matched += 1
    return matched / checked if checked else 0.0


def infer_temporal_constraints(entity: str, rows: list[dict[str, str]], fields: list[str]) -> list[Constraint]:
    constraints: list[Constraint] = []
    for start, end in combinations(fields, 2):
        confidence = temporal_confidence(rows, start, end)
        if confidence >= MIN_CONFIDENCE:
            constraints.append(
                Constraint(
                    type=ConstraintType.TEMPORAL,
                    entity=entity,
                    fields=[start, end],
                    confidence=round(confidence, 6),
                )
            )
        else:
            reverse = temporal_confidence(rows, end, start)
            if reverse >= MIN_CONFIDENCE:
                constraints.append(
                    Constraint(
                        type=ConstraintType.TEMPORAL,
                        entity=entity,
                        fields=[end, start],
                        confidence=round(reverse, 6),
                    )
                )
    return constraints


def temporal_confidence(rows: list[dict[str, str]], start: str, end: str) -> float:
    checked = 0
    matched = 0
    for row in rows:
        start_value = parse_datetime_value(row.get(start, ""))
        end_value = parse_datetime_value(row.get(end, ""))
        if start_value is None or end_value is None:
            continue
        checked += 1
        if start_value <= end_value:
            matched += 1
    return matched / checked if checked else 0.0


def infer_conditional_required_constraints(entity: str, rows: list[dict[str, str]], fields: list[Any]) -> list[Constraint]:
    constraints: list[Constraint] = []
    categorical_fields = [
        field for field in fields
        if field.distribution.get("kind") == "categorical" and len(field.distribution.get("categories", [])) <= 10
    ]
    nullable_fields = [field for field in fields if field.nullable]
    for condition_field in categorical_fields:
        values = [item["value"] for item in condition_field.distribution.get("categories", [])]
        for value in values:
            scoped_rows = [row for row in rows if row.get(condition_field.name) == value]
            if not scoped_rows:
                continue
            for required_field in nullable_fields:
                if required_field.name == condition_field.name:
                    continue
                confidence = sum(bool(row.get(required_field.name, "").strip()) for row in scoped_rows) / len(scoped_rows)
                global_presence = sum(bool(row.get(required_field.name, "").strip()) for row in rows) / len(rows) if rows else 0
                if confidence >= MIN_CONFIDENCE and confidence - global_presence >= 0.2:
                    constraints.append(
                        Constraint(
                            type=ConstraintType.CONDITIONAL_REQUIRED,
                            entity=entity,
                            fields=[required_field.name],
                            condition={"field": condition_field.name, "equals": value},
                            confidence=round(confidence, 6),
                        )
                    )
    return constraints


def infer_aggregate_mapping_constraints(profile: DatasetProfile) -> list[Constraint]:
    constraints: list[Constraint] = []
    for relationship in profile.relationships:
        parent = profile.entity(relationship.parent_entity)
        child = profile.entity(relationship.child_entity)
        parent_names = {field.name.lower(): field.name for field in parent.fields}
        child_numeric = [field for field in child.fields if field.data_type in {FieldType.INTEGER, FieldType.FLOAT} and not field.is_identifier]
        for child_field in child_numeric:
            total_name = f"{relationship.child_entity}_{child_field.name}_total"
            if total_name.lower() in parent_names:
                constraints.append(
                    Constraint(
                        type=ConstraintType.AGGREGATE_MAPPING,
                        entity=relationship.parent_entity,
                        fields=[parent_names[total_name.lower()]],
                        target_entity=relationship.child_entity,
                        target_field=child_field.name,
                        aggregate="sum",
                        confidence=0.8,
                    )
                )
    return constraints
