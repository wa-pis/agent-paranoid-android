"""Plan dataset generation from safe profile metadata."""

from __future__ import annotations

from collections.abc import Mapping

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.field import FieldSpec, FieldProfile, FieldType
from test_data_agent.core.inference import FieldInferenceEffect, InferenceEvidence, InferenceOptions
from test_data_agent.core.privacy import is_sensitive_field, validate_local_category_field
from test_data_agent.safety import assert_profile_safe, assert_spec_safe


def infer_dataset_spec(
    profile: DatasetProfile, count: int | None = None, *,
    decimal_fields: Mapping[str, FieldSpec] | None = None,
    entity_counts: Mapping[str, int] | None = None,
    max_total_rows: int | None = None,
    inference_options: InferenceOptions | None = None,
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
    preserved_categories = {(item.entity, item.field) for item in profile.local_category_fields}
    rules = inference_options.effective_rules() if inference_options is not None else ()
    if rules and sum(len(entity.fields) for entity in profile.entities) * len(rules) > 100_000:
        raise ValueError("inference rule evaluation limit exceeded")
    relationship_floor = inference_options.min_relationship_confidence if inference_options else 0.0
    constraint_floor = inference_options.min_constraint_confidence if inference_options else 0.0
    relationships = [
        edge for edge in profile.relationships
        if edge.status != "inferred" or edge.confidence >= relationship_floor
    ]
    constraints = [
        item for item in profile.constraints
        if item.status != "inferred" or item.confidence >= constraint_floor
    ]
    effects: list[FieldInferenceEffect] = []
    entities: list[EntitySpec] = []
    for entity_index, entity in enumerate(profile.entities):
        if any(field.null_ratio is None for field in entity.fields):
            raise ValueError("unknown null statistics require an explicit reviewed generation spec")
        primary_key = entity.primary_key_candidates[0] if entity.primary_key_candidates else None
        fields: list[FieldSpec] = []
        for field_index, field in enumerate(entity.fields):
            key = f"{entity.name}.{field.name}"
            custom_identifier = False
            if (
                rules and key not in overrides and field.data_type == FieldType.STRING
                and not field.is_identifier and (entity.name, field.name) not in preserved_categories
                and not (field.sensitive or is_sensitive_field(field.name, field.semantic_type))
            ):
                matches = [
                    (index, rule) for index, rule in enumerate(rules)
                    if (rule.entity is None or rule.entity == entity.name)
                    and field.name.endswith(rule.field_suffix)
                ]
                if matches:
                    index, winner = max(matches, key=lambda pair: pair[1].priority)
                    if any(rule.priority == winner.priority and rule.action != winner.action for _, rule in matches):
                        raise ValueError("conflicting inference rules; adjust the priority of matching rules")
                    custom_identifier = winner.action == "synthetic_identifier"
                    effects.append(FieldInferenceEffect(
                        entity_index=entity_index, field_index=field_index, rule_index=index, action=winner.action,
                    ))
            fields.append(_infer_field(
                field, overrides.get(key), csv_numeric_replacement=key in csv_replacement_names,
                custom_identifier=custom_identifier,
            ))
        entities.append(EntitySpec(name=entity.name, row_count=resolved_counts[entity.name],
                                  primary_key=primary_key, fields=fields))
    spec = DatasetSpec(
        entities=entities,
        relationships=relationships,
        constraints=constraints,
        local_category_fields=profile.local_category_fields,
        inference_evidence=InferenceEvidence(
            options_sha256=inference_options.fingerprint(),
            field_effects=effects,
            min_relationship_confidence=relationship_floor,
            min_constraint_confidence=constraint_floor,
            relationships_filtered=len(profile.relationships) - len(relationships),
            constraints_filtered=len(profile.constraints) - len(constraints),
        ) if inference_options is not None else None,
    )
    if overrides or inference_options is not None:
        assert_spec_safe(spec)
    return spec


def _infer_field(
    field: FieldProfile, reviewed: FieldSpec | None, *, csv_numeric_replacement: bool = False,
    custom_identifier: bool = False,
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
        semantic_type=field.semantic_type, is_identifier=field.is_identifier or custom_identifier,
        distribution={} if custom_identifier else field.distribution,
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
