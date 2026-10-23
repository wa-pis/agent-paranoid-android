"""Plan dataset generation from safe profile metadata."""

from __future__ import annotations

from collections.abc import Mapping

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.field import FieldSpec, FieldProfile, FieldType
from test_data_agent.core.privacy import is_sensitive_field, validate_local_category_field
from test_data_agent.safety import assert_profile_safe, assert_spec_safe


def infer_dataset_spec(
    profile: DatasetProfile, count: int | None = None, *,
    decimal_fields: Mapping[str, FieldSpec] | None = None,
    entity_counts: Mapping[str, int] | None = None,
    max_total_rows: int | None = None,
) -> DatasetSpec:
    assert_profile_safe(profile)
    if profile.source_type in {"postgres_query", "trino_query"} and profile.has_unmodeled_expressions is None:
        raise ValueError("SQL query profile requires reprofiling for expression dependency checks")
    if profile.has_unmodeled_expressions:
        raise ValueError("SQL expression dependencies are unsupported for inferred generation")
    counts = dict(entity_counts or {})
    if set(counts) - {entity.name for entity in profile.entities}:
        raise ValueError("entity counts must reference existing profile entities")
    if any(type(value) is not int or value <= 0 for value in counts.values()):
        raise ValueError("entity counts must be positive integers")
    if max_total_rows is not None and (type(max_total_rows) is not int or max_total_rows <= 0):
        raise ValueError("maximum total rows must be a positive integer")
    resolved_counts = {
        entity.name: counts.get(entity.name, count or max(entity.row_count, 1))
        for entity in profile.entities
    }
    if max_total_rows is not None and sum(resolved_counts.values()) > max_total_rows:
        raise ValueError("planned total rows exceed maximum total rows")
    overrides = decimal_fields or {}
    decimal_names = {
        f"{entity.name}.{field.name}" for entity in profile.entities
        for field in entity.fields if field.data_type == FieldType.DECIMAL
    }
    csv_replacement_names: set[str] = set()
    if profile.source_type in {"csv", "csv_folder"}:
        related = {(edge.parent_entity, edge.parent_field) for edge in profile.relationships}
        related.update((edge.child_entity, edge.child_field) for edge in profile.relationships)
        csv_replacement_names = {
            f"{entity.name}.{field.name}" for entity in profile.entities for field in entity.fields
            if (entity.name, field.name) not in related and field.name not in entity.primary_key_candidates
        }
    if set(overrides) - (decimal_names | csv_replacement_names):
        raise ValueError("reviewed decimal fields must match decimal profile fields or eligible CSV numeric fields")
    entities: list[EntitySpec] = []
    for entity in profile.entities:
        if any(field.null_ratio is None for field in entity.fields):
            raise ValueError("unknown null statistics require an explicit reviewed generation spec")
        primary_key = entity.primary_key_candidates[0] if entity.primary_key_candidates else None
        entities.append(
            EntitySpec(
                name=entity.name,
                row_count=resolved_counts[entity.name],
                primary_key=primary_key,
                fields=[
                    _infer_field(
                        field, overrides.get(f"{entity.name}.{field.name}"),
                        csv_numeric_replacement=f"{entity.name}.{field.name}" in csv_replacement_names,
                    )
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


def _infer_field(
    field: FieldProfile, reviewed: FieldSpec | None, *, csv_numeric_replacement: bool = False,
) -> FieldSpec:
    if reviewed is not None and csv_numeric_replacement and field.data_type != FieldType.DECIMAL:
        return _reviewed_csv_numeric_field(field, reviewed)
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


def _reviewed_csv_numeric_field(field: FieldProfile, reviewed: FieldSpec) -> FieldSpec:
    """Use an independently authored synthetic range, never source numeric bounds."""
    try:
        validate_local_category_field(
            field_name=field.name,
            semantic_type=None if field.semantic_type == "phone" else field.semantic_type,
            sensitive=field.sensitive and field.semantic_type != "phone",
        )
    except ValueError:
        raise ValueError("reviewed CSV numeric replacement cannot override protected field names") from None
    if field.is_identifier or (field.sensitive and field.semantic_type != "phone"):
        raise ValueError("reviewed CSV numeric replacement cannot override sensitive or identifier fields")
    if field.data_type not in {FieldType.INTEGER, FieldType.FLOAT} and field.numeric_storage_type is None:
        raise ValueError("reviewed CSV numeric replacement requires finite numeric storage evidence; reprofile the CSV")
    if (
        reviewed.name != field.name or reviewed.data_type != FieldType.DECIMAL
        or reviewed.semantic_type != "numeric_measure" or reviewed.sensitive or reviewed.is_identifier
        or not isinstance(reviewed.typed_distribution, DecimalRangeDistribution)
    ):
        raise ValueError("reviewed CSV numeric replacement requires a matching numeric_measure decimal_range field")
    return reviewed.model_copy(deep=True)
