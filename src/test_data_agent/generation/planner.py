"""Plan dataset generation from safe profile metadata."""

from __future__ import annotations

from collections.abc import Mapping

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.field import FieldSpec, FieldProfile, FieldType
from test_data_agent.core.privacy import is_sensitive_field
from test_data_agent.safety import assert_profile_safe, assert_spec_safe


def infer_dataset_spec(
    profile: DatasetProfile, count: int | None = None, *,
    decimal_fields: Mapping[str, FieldSpec] | None = None,
) -> DatasetSpec:
    assert_profile_safe(profile)
    if profile.source_type in {"postgres_query", "trino_query"} and profile.has_unmodeled_expressions is None:
        raise ValueError("SQL query profile requires reprofiling for expression dependency checks")
    if profile.has_unmodeled_expressions:
        raise ValueError("SQL expression dependencies are unsupported for inferred generation")
    overrides = decimal_fields or {}
    decimal_names = {
        f"{entity.name}.{field.name}" for entity in profile.entities
        for field in entity.fields if field.data_type == FieldType.DECIMAL
    }
    if set(overrides) - decimal_names:
        raise ValueError("reviewed decimal fields must match decimal profile fields")
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
                    _infer_field(field, overrides.get(f"{entity.name}.{field.name}"))
                    for field in entity.fields
                ],
            )
        )
    spec = DatasetSpec(
        entities=entities,
        relationships=profile.relationships,
        constraints=profile.constraints,
        local_category_fields=profile.local_category_fields,
    )
    if overrides:
        assert_spec_safe(spec)
    return spec


def _infer_field(field: FieldProfile, reviewed: FieldSpec | None) -> FieldSpec:
    if field.data_type == FieldType.DECIMAL:
        if reviewed is None:
            raise ValueError(
                "decimal fields require an exact decimal_range distribution; "
                "supply reviewed synthetic fields with --decimal-fields; source extrema are not inferred"
            )
        distribution = reviewed.typed_distribution
        if not isinstance(distribution, DecimalRangeDistribution) or reviewed.name != field.name:
            raise ValueError("reviewed decimal field does not match profile metadata")
        if field.decimal_precision is not None and (
            distribution.precision != field.decimal_precision or distribution.scale != field.decimal_scale
        ):
            raise ValueError("reviewed decimal precision and scale must match declared source type")
        if field.sensitive or field.is_identifier or is_sensitive_field(field.name, field.semantic_type):
            raise ValueError("sensitive decimal profile requires an independently authored safe specification")
        return reviewed.model_copy(deep=True)
    return FieldSpec(
        name=field.name, data_type=field.data_type, nullable=field.nullable,
        null_ratio=field.null_ratio if field.null_ratio is not None else 0.0,
        sensitive=field.sensitive or is_sensitive_field(field.name, field.semantic_type),
        semantic_type=field.semantic_type, is_identifier=field.is_identifier,
        distribution=field.distribution,
    )
