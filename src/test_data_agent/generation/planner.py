"""Plan dataset generation from safe profile metadata."""

from __future__ import annotations

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.privacy import is_sensitive_field
from test_data_agent.safety import assert_profile_safe


def infer_dataset_spec(profile: DatasetProfile, count: int | None = None) -> DatasetSpec:
    assert_profile_safe(profile)
    if profile.source_type in {"postgres_query", "trino_query"} and profile.has_unmodeled_expressions is None:
        raise ValueError("SQL query profile requires reprofiling for expression dependency checks")
    if profile.has_unmodeled_expressions:
        raise ValueError("SQL expression dependencies are unsupported for inferred generation")
    entities: list[EntitySpec] = []
    for entity in profile.entities:
        if any(field.null_ratio is None for field in entity.fields):
            raise ValueError("unknown null statistics require an explicit reviewed generation spec")
        primary_key = entity.primary_key_candidates[0] if entity.primary_key_candidates else None
        entities.append(
            EntitySpec(
                name=entity.name,
                row_count=count or max(entity.row_count, 1),
                primary_key=primary_key,
                fields=[
                    FieldSpec(
                        name=field.name,
                        data_type=field.data_type,
                        nullable=field.nullable,
                        null_ratio=field.null_ratio if field.null_ratio is not None else 0.0,
                        sensitive=field.sensitive or is_sensitive_field(field.name, field.semantic_type),
                        semantic_type=field.semantic_type,
                        is_identifier=field.is_identifier,
                        distribution=field.distribution,
                    )
                    for field in entity.fields
                ],
            )
        )
    return DatasetSpec(
        entities=entities,
        relationships=profile.relationships,
        constraints=profile.constraints,
        local_category_fields=profile.local_category_fields,
    )
