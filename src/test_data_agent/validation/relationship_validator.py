"""Relationship validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.relationship import RelationshipType


class RelationshipMetrics(BaseModel):
    parent_entity: str
    parent_field: str
    child_entity: str
    child_field: str
    parent_distinct_keys: int
    checked_references: int
    resolved_references: int
    null_references: int
    resolution_ratio: float | None
    valid: bool


def validate_relationships(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    *,
    empty_string_is_null: bool = True,
    budget: GenerationBudget | None = None,
    metrics: list[RelationshipMetrics] | None = None,
) -> list[str]:
    """Validate keys; legacy generated CSV treats empty text as a null marker."""
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    null_values = (None, "") if empty_string_is_null else (None,)
    errors: list[str] = []
    for relationship in budget.iter_rule_work(spec.relationships):
        if relationship.status == "rejected":
            continue
        previous_errors = len(errors)
        checked = resolved = nulls = 0
        child_field = spec.entity(relationship.child_entity).field(relationship.child_field)
        parent_values = {
            row.get(relationship.parent_field)
            for row in budget.iter_rule_work(rows_by_entity.get(relationship.parent_entity, []))
            if row.get(relationship.parent_field) is not None
        }
        for index, row in budget.iter_rule_work(enumerate(rows_by_entity.get(relationship.child_entity, []))):
            value = row.get(relationship.child_field)
            if value in null_values and child_field.nullable:
                nulls += 1
                continue
            checked += 1
            resolved += int(value in parent_values)
            if value not in parent_values:
                errors.append(f"{relationship.child_entity}[{index}].{relationship.child_field} has no parent")
        if relationship.relationship_type == RelationshipType.ONE_TO_ONE:
            child_values = [
                row.get(relationship.child_field)
                for row in budget.iter_rule_work(rows_by_entity.get(relationship.child_entity, []))
                if row.get(relationship.child_field) not in null_values
            ]
            duplicates = len(child_values) - len(set(child_values))
            errors.extend(
                f"{relationship.child_entity}.{relationship.child_field} violates one_to_one cardinality"
                for _ in budget.iter_rule_work(range(max(0, duplicates)))
            )
        if metrics is not None:
            metrics.append(RelationshipMetrics(
                parent_entity=relationship.parent_entity, parent_field=relationship.parent_field,
                child_entity=relationship.child_entity, child_field=relationship.child_field,
                parent_distinct_keys=len(parent_values), checked_references=checked,
                resolved_references=resolved, null_references=nulls,
                resolution_ratio=resolved / checked if checked else None,
                valid=len(errors) == previous_errors,
            ))
    return errors
