"""Relationship inference from example tables."""

from __future__ import annotations

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.relationship import Relationship


def infer_relationships(profile: DatasetProfile, rows_by_entity: dict[str, list[dict[str, str]]]) -> list[Relationship]:
    relationships: list[Relationship] = []
    parent_candidates = []
    for entity in profile.entities:
        for field_name in entity.primary_key_candidates:
            values = non_empty_values(rows_by_entity.get(entity.name, []), field_name)
            if values:
                parent_candidates.append((entity.name, field_name, set(values)))

    for child in profile.entities:
        for child_field in child.fields:
            if not child_field.is_identifier:
                continue
            child_values = non_empty_values(rows_by_entity.get(child.name, []), child_field.name)
            if not child_values:
                continue
            for parent_entity, parent_field, parent_values in parent_candidates:
                if parent_entity == child.name and parent_field == child_field.name:
                    continue
                overlap = sum(value in parent_values for value in child_values)
                confidence = overlap / len(child_values)
                if confidence >= 0.8:
                    relationships.append(
                        Relationship(
                            parent_entity=parent_entity,
                            parent_field=parent_field,
                            child_entity=child.name,
                            child_field=child_field.name,
                            confidence=round(confidence, 6),
                        )
                    )
    return dedupe_relationships(relationships)


def non_empty_values(rows: list[dict[str, str]], field: str) -> list[str]:
    return [value.strip() for row in rows if (value := row.get(field, "")).strip()]


def dedupe_relationships(relationships: list[Relationship]) -> list[Relationship]:
    best: dict[tuple[str, str], Relationship] = {}
    for relationship in relationships:
        key = (relationship.child_entity, relationship.child_field)
        if key not in best or relationship.confidence > best[key].confidence:
            best[key] = relationship
    return list(best.values())
