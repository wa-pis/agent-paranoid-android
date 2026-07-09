"""Normalize legacy profiles and specs into DatasetProfile and DatasetSpec."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
import warnings

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.distribution import CategoryWeight, MaskedPattern
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.field import FieldProfile, FieldSpec, FieldType
from test_data_agent.core.privacy import is_sensitive_field, mask_pattern
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationSettings, OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.generator import generate_rows
from test_data_agent.spec import (
    ColumnSpec,
    DataType,
    GenerationSpec,
    GenerationStrategy,
    MultiTableGenerationSpec,
    TableSpec,
    coerce_profile_type,
)
from test_data_agent.validator import ValidationReport, validate_rows_report


_LEGACY_COMPATIBILITY_WARNING = (
    "GenerationSpec compatibility is deprecated; prefer DatasetSpec and DatasetProfile APIs"
)


@dataclass(frozen=True)
class LegacyGenerationResult:
    spec: GenerationSpec
    dataset_spec: DatasetSpec
    rows: list[dict[str, Any]]
    report: ValidationReport


def _warn_legacy_compatibility() -> None:
    warnings.warn(_LEGACY_COMPATIBILITY_WARNING, DeprecationWarning, stacklevel=2)


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
    _warn_legacy_compatibility()
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


def generation_spec_to_dataset_spec(spec: GenerationSpec) -> DatasetSpec:
    entity = EntitySpec(
        name=spec.table.name,
        row_count=spec.table.row_count,
        fields=[_field_spec_from_column_spec(column) for column in spec.table.columns],
        primary_key=_primary_key_for_columns(spec.table.columns),
    )
    return DatasetSpec(
        entities=[entity],
        generation_settings=GenerationSettings(
            seed=spec.seed,
            output_format=OutputFormat(spec.output_format.value),
        ),
    )


def dataset_spec_from_generation_spec(spec: GenerationSpec) -> DatasetSpec:
    return generation_spec_to_dataset_spec(spec)


def multi_table_generation_spec_to_dataset_spec(spec: MultiTableGenerationSpec) -> DatasetSpec:
    entities = [
        EntitySpec(
            name=table.name,
            row_count=table.row_count,
            fields=[_field_spec_from_column_spec(column) for column in table.columns],
            primary_key=_primary_key_for_columns(table.columns),
        )
        for table in spec.tables
    ]
    relationships = [
        Relationship(
            parent_entity=foreign_key.parent_table,
            parent_field=foreign_key.parent_field,
            child_entity=foreign_key.child_table,
            child_field=foreign_key.child_field,
            confidence=1.0,
            status="configured",
        )
        for foreign_key in spec.foreign_keys
    ]
    return DatasetSpec(
        entities=entities,
        relationships=relationships,
        generation_settings=GenerationSettings(
            seed=spec.seed,
            output_format=OutputFormat(spec.output_format.value),
        ),
    )


def dataset_spec_to_generation_spec(
    spec: DatasetSpec,
    *,
    seed: int | None = None,
    output_format: OutputFormat | None = None,
) -> GenerationSpec:
    _warn_legacy_compatibility()
    if len(spec.entities) != 1:
        raise ValueError("legacy GenerationSpec compatibility requires exactly one entity")

    entity = spec.entities[0]
    return GenerationSpec(
        seed=spec.generation_settings.seed if seed is None else seed,
        table=TableSpec(
            name=entity.name,
            row_count=entity.row_count,
            columns=[_column_spec_from_field_spec(field) for field in entity.fields],
        ),
        output_format=output_format or spec.generation_settings.output_format,
    )


def generate_legacy_rows(spec: GenerationSpec) -> list[dict[str, Any]]:
    _warn_legacy_compatibility()
    return generate_rows(spec)


def validate_legacy_rows_report(rows: list[dict[str, Any]], spec: GenerationSpec) -> ValidationReport:
    _warn_legacy_compatibility()
    return validate_rows_report(rows, spec)


def load_legacy_generation_spec(path: Path) -> GenerationSpec:
    _warn_legacy_compatibility()
    return GenerationSpec.model_validate_json(path.read_text())


def prepare_legacy_generation_spec(
    path: Path,
    *,
    row_count: int | None = None,
    seed: int | None = None,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
) -> GenerationSpec:
    spec = load_legacy_generation_spec(path)
    if row_count is not None:
        spec.table.row_count = row_count
    if seed is not None:
        spec.seed = seed
    if output_format is not None:
        spec.output_format = output_format
    apply_legacy_mode_options(spec, mode=mode, invalid_ratio=invalid_ratio)
    return spec


def generate_legacy_compatibility_result(
    path: Path,
    *,
    row_count: int | None = None,
    seed: int | None = None,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
) -> LegacyGenerationResult:
    spec = prepare_legacy_generation_spec(
        path,
        row_count=row_count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    dataset_spec = generation_spec_to_dataset_spec(spec)
    rows = next(iter(generate_dataset(spec=dataset_spec, seed=spec.seed or 0).values()))
    report = validate_legacy_rows_report(rows, spec)
    return LegacyGenerationResult(
        spec=spec,
        dataset_spec=dataset_spec,
        rows=rows,
        report=report,
    )


def validate_legacy_rows_file(
    spec_path: Path,
    rows_path: Path,
) -> ValidationReport:
    spec = prepare_legacy_generation_spec(spec_path)
    rows = json.loads(rows_path.read_text())
    return validate_legacy_rows_report(rows, spec)


def apply_legacy_mode_options(spec: GenerationSpec, *, mode: str, invalid_ratio: float) -> None:
    if mode in {"mixed", "negative"}:
        if not 0.0 <= invalid_ratio <= 1.0:
            raise SystemExit("--invalid-ratio must be between 0 and 1")
        for column in spec.table.columns:
            column.invalid_ratio = 1.0 if mode == "negative" else invalid_ratio
        return
    if invalid_ratio:
        raise SystemExit("--invalid-ratio requires --mode mixed or --mode negative")


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


def _field_spec_from_column_spec(column: ColumnSpec) -> FieldSpec:
    return FieldSpec(
        name=column.name,
        data_type=_field_type_from_legacy_type(column.data_type),
        nullable=column.nullable,
        null_ratio=column.null_probability,
        sensitive=bool(column.sensitive),
        semantic_type=_semantic_type_for_data_type(column.data_type),
        is_identifier=_is_identifier(column.name, 1.0)
        or column.strategy in {GenerationStrategy.SEQUENCE, GenerationStrategy.UUID},
        distribution=_distribution_from_generation_column(column),
    )


def _column_spec_from_field_spec(field: FieldSpec) -> ColumnSpec:
    data_type = _legacy_type_from_field_spec(field)
    distribution = field.distribution
    kind = str(distribution.get("kind") or "")

    strategy: GenerationStrategy | None = None
    faker_provider: str | None = None
    choices: list[Any] | None = None

    if field.is_identifier:
        strategy = GenerationStrategy.SEQUENCE if data_type == DataType.INTEGER else GenerationStrategy.UUID
    elif field.sensitive:
        strategy = GenerationStrategy.FAKER
        faker_provider = _faker_provider_for_data_type(data_type)
    elif kind == "categorical":
        raw_categories = distribution.get("categories") or []
        choices = [item.get("value") for item in raw_categories if isinstance(item, Mapping) and item.get("value") is not None]
        strategy = GenerationStrategy.CHOICE if choices else None
    elif data_type == DataType.DATE:
        strategy = GenerationStrategy.DATE_RANGE
    elif data_type == DataType.DATETIME:
        strategy = GenerationStrategy.DATETIME_RANGE

    return ColumnSpec(
        name=field.name,
        data_type=data_type,
        nullable=field.nullable,
        sensitive=field.sensitive,
        strategy=strategy,
        faker_provider=faker_provider,
        choices=choices,
        min_value=_numeric_value(distribution, data_type, "p05", "min_value"),
        max_value=_numeric_value(distribution, data_type, "p95", "max_value"),
        min_date=distribution.get("min") if data_type == DataType.DATE else None,
        max_date=distribution.get("max") if data_type == DataType.DATE else None,
        min_datetime=distribution.get("min") if data_type == DataType.DATETIME else None,
        max_datetime=distribution.get("max") if data_type == DataType.DATETIME else None,
        null_probability=field.null_ratio if field.nullable else 0.0,
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


def _legacy_type_from_field_spec(field: FieldSpec) -> DataType:
    semantic_type = field.semantic_type or ""
    if semantic_type == "email":
        return DataType.EMAIL
    if semantic_type == "phone":
        return DataType.PHONE
    if semantic_type == "name":
        return DataType.NAME
    if semantic_type == "address":
        return DataType.ADDRESS
    if field.data_type == FieldType.INTEGER:
        return DataType.INTEGER
    if field.data_type == FieldType.FLOAT:
        return DataType.FLOAT
    if field.data_type == FieldType.BOOLEAN:
        return DataType.BOOLEAN
    if field.data_type == FieldType.DATE:
        return DataType.DATE
    if field.data_type == FieldType.DATETIME:
        return DataType.DATETIME
    return DataType.STRING


def _semantic_type_for_data_type(data_type: DataType) -> str | None:
    if data_type in {DataType.EMAIL, DataType.PHONE, DataType.NAME, DataType.ADDRESS}:
        return data_type.value
    return None


def _faker_provider_for_data_type(data_type: DataType) -> str:
    if data_type == DataType.EMAIL:
        return "email"
    if data_type == DataType.PHONE:
        return "phone_number"
    if data_type == DataType.NAME:
        return "name"
    if data_type == DataType.ADDRESS:
        return "address"
    return "word"


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
                MaskedPattern(pattern=mask_pattern(str(item.get("value", "")), semantic_type), count=int(item.get("count", 0) or 0)).model_dump(mode="json")
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


def _distribution_from_generation_column(column: ColumnSpec) -> dict[str, Any]:
    if column.strategy in {GenerationStrategy.SEQUENCE, GenerationStrategy.UUID}:
        return {"kind": "synthetic_identifier", "prefix": _identifier_prefix(column.name, column.name)}
    if column.strategy == GenerationStrategy.CHOICE:
        return {
            "kind": "categorical",
            "categories": [
                CategoryWeight(value=value, count=1.0).model_dump(mode="json")
                for value in (column.choices or [])
            ],
        }
    if column.strategy == GenerationStrategy.RANDOM_BOOLEAN:
        return {"kind": "boolean", "true_ratio": 0.5}
    if column.strategy in {GenerationStrategy.RANDOM_INT, GenerationStrategy.RANDOM_FLOAT}:
        return {
            "kind": "numeric",
            "min_value": column.min_value,
            "max_value": column.max_value,
            "p05": column.min_value,
            "p95": column.max_value,
        }
    if column.strategy == GenerationStrategy.DATE_RANGE:
        return {
            "kind": "date_range",
            "min": column.min_date.isoformat() if column.min_date is not None else None,
            "max": column.max_date.isoformat() if column.max_date is not None else None,
        }
    if column.strategy == GenerationStrategy.DATETIME_RANGE:
        return {
            "kind": "datetime_range",
            "min": column.min_datetime.isoformat() if column.min_datetime is not None else None,
            "max": column.max_datetime.isoformat() if column.max_datetime is not None else None,
        }
    if column.strategy == GenerationStrategy.CONSTANT:
        return {
            "kind": "categorical",
            "categories": [CategoryWeight(value=column.constant, count=1.0).model_dump(mode="json")],
        }
    return {}


def _primary_key_for_columns(columns: list[ColumnSpec]) -> str | None:
    for column in columns:
        if column.strategy in {GenerationStrategy.SEQUENCE, GenerationStrategy.UUID}:
            return column.name
    for column in columns:
        if _is_identifier(column.name, 1.0):
            return column.name
    return None


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


def _numeric_value(
    distribution: Mapping[str, Any],
    data_type: DataType,
    preferred_key: str,
    fallback_key: str,
) -> int | float | None:
    if data_type not in {DataType.INTEGER, DataType.FLOAT}:
        return None
    value = distribution.get(preferred_key, distribution.get(fallback_key))
    if value is None:
        return None
    if data_type == DataType.INTEGER:
        return int(round(float(value)))
    return float(value)
