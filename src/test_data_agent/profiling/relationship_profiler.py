"""Relationship inference from example tables."""

from __future__ import annotations

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.relationship import Relationship
from test_data_agent.profiling.budget import LocalProfileBudget


def infer_relationships(profile: DatasetProfile, rows_by_entity: dict[str, list[dict[str, str]]], *, budget: LocalProfileBudget | None = None) -> list[Relationship]:
    work_budget = budget or LocalProfileBudget()
    relationships: list[Relationship] = []
    parent_candidates = []
    for entity in profile.entities:
        for field_name in entity.primary_key_candidates:
            values = non_empty_values(rows_by_entity.get(entity.name, []), field_name, budget=work_budget)
            if values:
                parent_candidates.append((entity.name, field_name, entity.field(field_name).data_type, set(values)))

    for child in profile.entities:
        for child_field in child.fields:
            if not child_field.is_identifier:
                continue
            child_values = non_empty_values(rows_by_entity.get(child.name, []), child_field.name, budget=work_budget)
            if not child_values:
                continue
            for parent_entity, parent_field, parent_type, parent_values in parent_candidates:
                # Overlapping independent key domains are not relationship evidence.
                if (child_field.name != parent_field or child_field.data_type != parent_type
                        or parent_field.lower() in {"id", "key", "uuid"}):
                    continue
                if parent_entity == child.name and parent_field == child_field.name:
                    continue
                work_budget.consume_inference_evaluation()
                overlap = 0
                for value in child_values:
                    work_budget.consume_inference_evaluation()
                    overlap += value in parent_values
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


def non_empty_values(rows: list[dict[str, str]], field: str, *, budget: LocalProfileBudget | None = None) -> list[str]:
    work_budget = budget or LocalProfileBudget()
    values = []
    for row in rows:
        work_budget.consume_inference_evaluation()
        if (value := row.get(field, "")).strip():
            values.append(value.strip())
    return values


def dedupe_relationships(relationships: list[Relationship]) -> list[Relationship]:
    candidates: dict[tuple[str, str], list[Relationship]] = {}
    for relationship in relationships:
        key = (relationship.child_entity, relationship.child_field)
        candidates.setdefault(key, []).append(relationship)
    # Competing parent domains require an explicit reviewed binding.
    return [items[0] for items in candidates.values() if len(items) == 1]
