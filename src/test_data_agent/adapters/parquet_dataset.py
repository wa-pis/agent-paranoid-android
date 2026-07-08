"""Parquet metadata adapters for DatasetProfile and DatasetSpec."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.csv_profiler import CSVProfile, CSVColumnProfile
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile, csv_profile_to_dataset_spec


def parquet_file_to_dataset_profile(path: Path, table_name: str | None = None) -> DatasetProfile:
    return csv_profile_to_dataset_profile(_parquet_metadata_as_csv_profile(path, table_name=table_name))


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


def _parquet_metadata_as_csv_profile(path: Path, table_name: str | None = None) -> CSVProfile:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("Parquet adapters require pyarrow") from exc

    parquet_file = pq.ParquetFile(path)
    arrow_schema = parquet_file.schema_arrow
    row_count = parquet_file.metadata.num_rows if parquet_file.metadata is not None else 0
    columns = [
        CSVColumnProfile(
            name=field.name,
            data_type=_csv_data_type_from_arrow(field.type),
            nullable=field.nullable,
            null_count=0,
            null_ratio=0.0,
            approx_distinct_count=0,
            sensitive=False,
        )
        for field in arrow_schema
    ]
    return CSVProfile(
        source_type="parquet",
        table=table_name or path.stem,
        row_count=row_count,
        columns=columns,
    )


def _csv_data_type_from_arrow(arrow_type: object) -> str:
    name = str(arrow_type).lower()
    if any(part in name for part in ("int", "uint")):
        return "integer"
    if any(part in name for part in ("float", "double", "decimal")):
        return "float"
    if name == "bool":
        return "boolean"
    if "timestamp" in name:
        return "datetime"
    if name == "date32[day]" or name == "date64[ms]":
        return "date"
    return "string"
