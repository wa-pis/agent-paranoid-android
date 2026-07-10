"""Plan dataset generation from safe profile metadata."""

from __future__ import annotations

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.privacy import is_sensitive_field
from test_data_agent.safety import assert_profile_safe


def infer_dataset_spec(profile: DatasetProfile, count: int | None = None) -> DatasetSpec:
    assert_profile_safe(profile)
    entities: list[EntitySpec] = []
    for entity in profile.entities:
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
                        null_ratio=field.null_ratio,
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
    )
