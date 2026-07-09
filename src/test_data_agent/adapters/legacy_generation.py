"""Normalize deprecated GenerationSpec helpers into DatasetSpec workflows."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
import warnings

from test_data_agent.adapters.legacy_profile import (
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
    legacy_profile_to_generation_spec,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.distribution import (
    CategoricalDistribution,
    CategoryWeight,
    DateRangeDistribution,
    DateTimeRangeDistribution,
    NumericDistribution,
)
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationSettings, OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generator import generate_rows
from test_data_agent.spec import (
    ColumnSpec,
    DataType,
    GenerationSpec,
    GenerationStrategy,
    MultiTableGenerationSpec,
    TableSpec,
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
    typed_distribution = field.typed_distribution

    strategy: GenerationStrategy | None = None
    faker_provider: str | None = None
    choices: list[Any] | None = None

    if field.is_identifier:
        strategy = GenerationStrategy.SEQUENCE if data_type == DataType.INTEGER else GenerationStrategy.UUID
    elif field.sensitive:
        strategy = GenerationStrategy.FAKER
        faker_provider = _faker_provider_for_data_type(data_type)
    elif isinstance(typed_distribution, CategoricalDistribution):
        choices = [category.value for category in typed_distribution.categories if category.value is not None]
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
        min_value=_numeric_value(field, distribution, data_type, "p05", "min_value"),
        max_value=_numeric_value(field, distribution, data_type, "p95", "max_value"),
        min_date=_distribution_min(field, distribution, data_type, DataType.DATE),
        max_date=_distribution_max(field, distribution, data_type, DataType.DATE),
        min_datetime=_distribution_min(field, distribution, data_type, DataType.DATETIME),
        max_datetime=_distribution_max(field, distribution, data_type, DataType.DATETIME),
        null_probability=field.null_ratio if field.nullable else 0.0,
    )


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


def _numeric_value(
    field: FieldSpec,
    distribution: Mapping[str, Any],
    data_type: DataType,
    preferred_key: str,
    fallback_key: str,
) -> int | float | None:
    if data_type not in {DataType.INTEGER, DataType.FLOAT}:
        return None
    typed_distribution = field.typed_distribution
    if typed_distribution is not None:
        if isinstance(typed_distribution, NumericDistribution):
            value = getattr(typed_distribution, preferred_key)
            if value is None:
                value = getattr(typed_distribution, fallback_key)
        else:
            value = None
    else:
        value = distribution.get(preferred_key, distribution.get(fallback_key))
    if value is None:
        return None
    if data_type == DataType.INTEGER:
        return int(round(float(value)))
    return float(value)


def _distribution_min(
    field: FieldSpec,
    distribution: Mapping[str, Any],
    data_type: DataType,
    expected_type: DataType,
) -> str | None:
    if data_type != expected_type:
        return None
    typed_distribution = field.typed_distribution
    if typed_distribution is not None:
        if isinstance(typed_distribution, DateRangeDistribution | DateTimeRangeDistribution):
            return typed_distribution.min
        return None
    value = distribution.get("min")
    return str(value) if value is not None else None


def _distribution_max(
    field: FieldSpec,
    distribution: Mapping[str, Any],
    data_type: DataType,
    expected_type: DataType,
) -> str | None:
    if data_type != expected_type:
        return None
    typed_distribution = field.typed_distribution
    if typed_distribution is not None:
        if isinstance(typed_distribution, DateRangeDistribution | DateTimeRangeDistribution):
            return typed_distribution.max
        return None
    value = distribution.get("max")
    return str(value) if value is not None else None
