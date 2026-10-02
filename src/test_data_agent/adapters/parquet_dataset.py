"""Parquet metadata adapters for DatasetProfile and DatasetSpec."""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import (
    InputLimitError, enforce_input_files, enforce_parquet_metadata_limits,
    max_input_cell_chars, max_parquet_expanded_bytes,
)
from test_data_agent.core.privacy import infer_sensitive_from_name, infer_sensitive_value_type
from test_data_agent.csv_profiler import CSVProfile, CSVColumnProfile
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile, csv_profile_to_dataset_spec
from test_data_agent.profiling.budget import LocalProfileBudget


def parquet_file_to_dataset_profile(path: Path, table_name: str | None = None) -> DatasetProfile:
    profile = csv_profile_to_dataset_profile(_parquet_metadata_as_csv_profile(path, table_name=table_name))
    profile.source_type = "parquet"
    return profile


def parquet_file_to_dataset_spec(
    path: Path,
    *,
    table_name: str | None = None,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return csv_profile_to_dataset_spec(
        _parquet_metadata_as_csv_profile(path, table_name=table_name),
        count=count,
        seed=seed,
    )


def dataset_profile_from_parquet(path: Path, table_name: str | None = None) -> DatasetProfile:
    return parquet_file_to_dataset_profile(path, table_name=table_name)


def dataset_spec_from_parquet(
    path: Path,
    *,
    table_name: str | None = None,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return parquet_file_to_dataset_spec(
        path,
        table_name=table_name,
        count=count,
        seed=seed,
    )


def _parquet_metadata_as_csv_profile(path: Path, table_name: str | None = None) -> CSVProfile:
    budget = LocalProfileBudget()
    budget.check_deadline("Parquet profiling preflight")
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("Parquet adapters require pyarrow") from exc

    enforce_input_files([path])
    parquet_file = pq.ParquetFile(path)
    enforce_parquet_metadata_limits(parquet_file.metadata, label=f"Parquet {path.name!r}")
    arrow_schema = parquet_file.schema_arrow
    row_count = parquet_file.metadata.num_rows if parquet_file.metadata is not None else 0
    sensitive = _parquet_sensitive_columns(parquet_file, budget=budget)
    columns = []
    for index, field in enumerate(arrow_schema):
        budget.check_deadline("Parquet field metadata")
        null_count = _parquet_null_count(parquet_file.metadata, index, field.name)
        columns.append(CSVColumnProfile(
            name=field.name,
            data_type=_csv_data_type_from_arrow(field.type),
            decimal_precision=field.type.precision if str(field.type).startswith("decimal") else None,
            decimal_scale=field.type.scale if str(field.type).startswith("decimal") else None,
            nullable=field.nullable,
            null_count=null_count,
            null_ratio=(round(null_count / row_count, 6) if row_count else 0.0)
            if null_count is not None else None,
            approx_distinct_count=None,
            sensitive=sensitive[index],
        ))
    budget.check_deadline("Parquet profile complete")
    return CSVProfile(
        source_type="parquet",
        table=table_name or path.stem,
        row_count=row_count,
        columns=columns,
    )


def _parquet_sensitive_columns(parquet_file: Any, *, budget: LocalProfileBudget | None = None) -> list[bool]:
    """Inspect bounded local values; retain only sensitivity flags, never rows."""
    flags = [infer_sensitive_from_name(field.name) for field in parquet_file.schema_arrow]
    budget = budget or LocalProfileBudget()
    expanded_limit = max_parquet_expanded_bytes()
    char_limit = max_input_cell_chars()
    expanded = 0
    for batch in parquet_file.iter_batches(batch_size=256):
        budget.check_deadline("Parquet sensitivity inspection")
        expanded += batch.nbytes
        if expanded > expanded_limit:
            raise InputLimitError("Parquet sensitivity inspection exceeded expanded byte budget")
        for index, column in enumerate(batch.columns):
            for scalar in column:
                budget.check_deadline("Parquet sensitivity inspection")
                value = scalar.as_py()
                if isinstance(value, (str, bytes)) and len(value) > char_limit:
                    raise InputLimitError("Parquet sensitivity inspection exceeded cell size budget")
                # This representation is inspection-only, never native matching.
                evidence = str(value) if type(value) in (int, float, Decimal) else value
                # Binary/composite content is unsupported evidence, not proof of safety.
                if isinstance(value, (bytes, list, tuple, dict)) or infer_sensitive_value_type(evidence):
                    flags[index] = True
    budget.check_deadline("Parquet sensitivity inspection")
    return flags


def _parquet_null_count(metadata: Any, index: int, field_name: str) -> int | None:
    """Use only complete, consistent flat-column row-group statistics."""
    if metadata is None or index >= metadata.num_columns:
        return None
    total = 0
    rows = 0
    for row_group_index in range(metadata.num_row_groups):
        row_group = metadata.row_group(row_group_index)
        rows += row_group.num_rows
        column = row_group.column(index)
        stats = column.statistics
        if column.path_in_schema != field_name or stats is None or not stats.has_null_count:
            return None
        count = stats.null_count
        if type(count) is not int or count < 0 or count > row_group.num_rows:
            return None
        total += count
    return total if rows == metadata.num_rows and total <= rows else None


def _csv_data_type_from_arrow(arrow_type: object) -> str:
    name = str(arrow_type).lower()
    if name.startswith("decimal"):
        return "decimal"
    if any(part in name for part in ("int", "uint")):
        return "integer"
    if any(part in name for part in ("float", "double")):
        return "float"
    if name == "bool":
        return "boolean"
    if "timestamp" in name:
        return "datetime"
    if name == "date32[day]" or name == "date64[ms]":
        return "date"
    return "string"
