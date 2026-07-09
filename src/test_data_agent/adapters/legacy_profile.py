"""Normalize legacy profile payloads into DatasetProfile and DatasetSpec."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import warnings

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.distribution import CategoryWeight, MaskedPattern
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.privacy import is_sensitive_field, mask_pattern
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.spec import DataType, GenerationSpec, coerce_profile_type


_LEGACY_COMPATIBILITY_WARNING = (
    "GenerationSpec compatibility is deprecated; prefer DatasetSpec and DatasetProfile APIs"
)


def legacy_profile_to_dataset_profile(
    profile: Mapping[str, Any],
    *,
    source_type: str = "legacy_profile",
) -> DatasetProfile:
    table_name = str(profile.get("table", "synthetic_table"))
    row_count = int(profile.get("row_count", 0) or 0)
    field_profiles = [
        _field_profile_from_column(table_name, row_count, column)
        for column in profile.get("columns", [])
    ]

    primary_key_candidates = [
        field.name
        for field in field_profiles
        if field.is_identifier and field.unique_ratio >= 1.0
    ]

    return DatasetProfile(
        source_type=source_type,
        entities=[
            EntityProfile(
                name=table_name,
                row_count=row_count,
                fields=field_profiles,
                primary_key_candidates=primary_key_candidates,
            )
        ],
    )


def legacy_profile_to_dataset_spec(
    profile: Mapping[str, Any],
    *,
    count: int | None = None,
    seed: int | None = None,
    source_type: str = "legacy_profile",
) -> DatasetSpec:
    dataset_spec = infer_dataset_spec(
        legacy_profile_to_dataset_profile(profile, source_type=source_type),
        count=count,
    )
    if seed is not None:
        dataset_spec.generation_settings.seed = seed
    return dataset_spec


def legacy_profile_to_generation_spec(
    profile: Mapping[str, Any],
    *,
    count: int,
    seed: int,
    output_format: OutputFormat = OutputFormat.JSON,
    source_type: str = "legacy_profile",
) -> GenerationSpec:
    warnings.warn(_LEGACY_COMPATIBILITY_WARNING, DeprecationWarning, stacklevel=2)

    from test_data_agent.adapters.legacy_generation import dataset_spec_to_generation_spec

    dataset_spec = legacy_profile_to_dataset_spec(
        profile,
        count=count,
        seed=seed,
        source_type=source_type,
    )
    return dataset_spec_to_generation_spec(
        dataset_spec,
        seed=seed,
        output_format=output_format,
    )


def _field_profile_from_column(
    table_name: str,
    row_count: int,
    column: Mapping[str, Any],
) -> FieldProfile:
    name = str(column.get("name", "column"))
    unique_ratio = _safe_ratio(column.get("approx_distinct_count"), row_count)
    is_identifier = _is_identifier(name, unique_ratio)
    semantic_type = _optional_string(column.get("semantic_type"))
    sensitive = bool(column.get("sensitive", False)) or is_sensitive_field(name, semantic_type)
    return FieldProfile(
        name=name,
        data_type=_field_type_from_raw(column.get("data_type", "string")),
        nullable=bool(column.get("nullable", False)),
        null_ratio=float(column.get("null_ratio", 0.0) or 0.0),
        unique_ratio=unique_ratio,
        sensitive=sensitive,
        semantic_type=semantic_type,
        is_identifier=is_identifier,
        distribution=_distribution_from_profile_column(name, table_name, is_identifier, sensitive, semantic_type, column),
    )


def _field_type_from_raw(value: Any) -> FieldType:
    if isinstance(value, DataType):
        return _field_type_from_legacy_type(value)
    normalized = str(value).lower()
    if normalized == FieldType.INTEGER.value:
        return FieldType.INTEGER
    if normalized == FieldType.FLOAT.value:
        return FieldType.FLOAT
    if normalized == FieldType.BOOLEAN.value:
        return FieldType.BOOLEAN
    if normalized == FieldType.DATE.value:
        return FieldType.DATE
    if normalized == FieldType.DATETIME.value:
        return FieldType.DATETIME
    coerced = coerce_profile_type(normalized)
    if coerced in {DataType.EMAIL, DataType.PHONE, DataType.NAME, DataType.ADDRESS}:
        return FieldType.STRING
    return _field_type_from_legacy_type(coerced)


def _field_type_from_legacy_type(data_type: DataType) -> FieldType:
    if data_type == DataType.INTEGER:
        return FieldType.INTEGER
    if data_type == DataType.FLOAT:
        return FieldType.FLOAT
    if data_type == DataType.BOOLEAN:
        return FieldType.BOOLEAN
    if data_type == DataType.DATE:
        return FieldType.DATE
    if data_type == DataType.DATETIME:
        return FieldType.DATETIME
    return FieldType.STRING


def _distribution_from_profile_column(
    name: str,
    table_name: str,
    is_identifier: bool,
    sensitive: bool,
    semantic_type: str | None,
    column: Mapping[str, Any],
) -> dict[str, Any]:
    top_values = column.get("top_values") or []
    masked_patterns = column.get("masked_patterns") or []
    if is_identifier:
        return {"kind": "synthetic_identifier", "prefix": _identifier_prefix(name, table_name)}
    if masked_patterns:
        return {
            "kind": "masked_patterns",
            "patterns": [MaskedPattern.model_validate(item).model_dump(mode="json") for item in masked_patterns],
        }
    if sensitive and top_values:
        return {
            "kind": "masked_patterns",
            "patterns": [
                MaskedPattern(
                    pattern=mask_pattern(str(item.get("value", "")), semantic_type),
                    count=int(item.get("count", 0) or 0),
                ).model_dump(mode="json")
                for item in top_values
            ],
        }
    if top_values:
        return {
            "kind": "categorical",
            "categories": [
                CategoryWeight(value=item.get("value"), count=float(item.get("count", 0) or 0)).model_dump(mode="json")
                for item in top_values
            ],
        }

    numeric_distribution = {
        "kind": "numeric",
        "min_value": column.get("min_value"),
        "max_value": column.get("max_value"),
        "p05": column.get("p05"),
        "p95": column.get("p95"),
    }
    if any(value is not None for key, value in numeric_distribution.items() if key != "kind"):
        return numeric_distribution

    if column.get("min_date") is not None or column.get("max_date") is not None:
        return {"kind": "date_range", "min": column.get("min_date"), "max": column.get("max_date")}
    if column.get("min_timestamp") is not None or column.get("max_timestamp") is not None:
        return {"kind": "datetime_range", "min": column.get("min_timestamp"), "max": column.get("max_timestamp")}
    return {}


def _is_identifier(name: str, unique_ratio: float) -> bool:
    del unique_ratio
    normalized = name.lower()
    return normalized == "id" or normalized.endswith("_id")


def _identifier_prefix(name: str, table_name: str) -> str:
    stem = name.removesuffix("_id")
    if stem and stem != name:
        return f"{stem.upper()}-"
    return f"{table_name.upper()}-"


def _optional_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _safe_ratio(distinct_count: Any, row_count: int) -> float:
    if row_count <= 0:
        return 0.0
    try:
        return min(max(float(distinct_count or 0) / row_count, 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "legacy_profile_to_dataset_profile",
    "legacy_profile_to_dataset_spec",
    "legacy_profile_to_generation_spec",
]
