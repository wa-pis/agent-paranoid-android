"""Relationship validation."""

from __future__ import annotations

from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.relationship import RelationshipType


def validate_relationships(rows_by_entity: dict[str, list[dict[str, Any]]], spec: DatasetSpec) -> list[str]:
    errors: list[str] = []
    for relationship in spec.relationships:
        parent_values = {
            row.get(relationship.parent_field)
            for row in rows_by_entity.get(relationship.parent_entity, [])
            if row.get(relationship.parent_field) is not None
        }
        for index, row in enumerate(rows_by_entity.get(relationship.child_entity, [])):
            value = row.get(relationship.child_field)
            if value not in parent_values:
                errors.append(f"{relationship.child_entity}[{index}].{relationship.child_field} has no parent")
        if relationship.relationship_type == RelationshipType.ONE_TO_ONE:
            child_values = [
                row.get(relationship.child_field)
                for row in rows_by_entity.get(relationship.child_entity, [])
                if row.get(relationship.child_field) is not None
            ]
            duplicates = len(child_values) - len(set(child_values))
            errors.extend(
                f"{relationship.child_entity}.{relationship.child_field} violates one_to_one cardinality"
                for _ in range(max(0, duplicates))
            )
    return errors
