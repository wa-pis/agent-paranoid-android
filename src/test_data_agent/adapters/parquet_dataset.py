"""Parquet metadata adapters for DatasetProfile and DatasetSpec."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
from pathlib import Path
from decimal import Decimal
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import (
    InputLimitError, enforce_input_files, enforce_parquet_metadata_limits,
)
from test_data_agent.core.parquet_limits import inspect_parquet_batch
from test_data_agent.core.privacy import infer_sensitive_from_name, infer_sensitive_value_type
from test_data_agent.csv_profiler import CSVProfile, CSVColumnProfile
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.profiling.budget import LocalProfileBudget


def parquet_file_to_dataset_profile(path: Path, table_name: str | None = None) -> DatasetProfile:
    return _parquet_dataset_profile(path, table_name=table_name)


def parquet_file_to_dataset_spec(
    path: Path,
    *,
    table_name: str | None = None,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    spec = infer_dataset_spec(parquet_file_to_dataset_profile(path, table_name=table_name), count=count)
    if seed is not None:
        spec.generation_settings.seed = seed
    return spec


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


def _parquet_dataset_profile(path: Path, table_name: str | None = None) -> DatasetProfile:
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
    evidence = _inspect_parquet_columns(parquet_file, budget=budget)
    columns = []
    for index, arrow_field in enumerate(arrow_schema):
        budget.check_deadline("Parquet field metadata")
        null_count = _parquet_null_count(parquet_file.metadata, index, arrow_field.name)
        columns.append(CSVColumnProfile(
            name=arrow_field.name,
            data_type=_csv_data_type_from_arrow(arrow_field.type),
            decimal_precision=arrow_field.type.precision if str(arrow_field.type).startswith("decimal") else None,
            decimal_scale=arrow_field.type.scale if str(arrow_field.type).startswith("decimal") else None,
            nullable=arrow_field.nullable,
            null_count=null_count,
            null_ratio=(round(null_count / row_count, 6) if row_count else 0.0)
            if null_count is not None else None,
            approx_distinct_count=None,
            sensitive=evidence[index].sensitive,
        ))
    budget.check_deadline("Parquet profile complete")
    profile = csv_profile_to_dataset_profile(CSVProfile(
        source_type="parquet", table=table_name or path.stem,
        row_count=row_count, columns=columns,
    ))
    profile.source_type = "parquet"
    entity = profile.entities[0]
    for result, observed in zip(entity.fields, evidence, strict=True):
        budget.check_deadline("Parquet distinct evidence")
        if observed.rows != row_count:
            raise InputLimitError("Parquet inspection row count is inconsistent")
        if observed.unknown:
            continue
        result.unique_ratio = len(observed.digests) / observed.non_null if observed.non_null else 0.0
        result.unique_ratio_kind = "lower_bound" if observed.overflow else "exact"
    # Distinct counts alone do not establish a semantic primary key or relationship.
    budget.check_deadline("Parquet profile complete")
    return profile


def _parquet_sensitive_columns(parquet_file: Any, *, budget: LocalProfileBudget | None = None) -> list[bool]:
    """Compatibility helper for the existing bounded sensitivity inspection."""
    return [item.sensitive for item in _inspect_parquet_columns(parquet_file, budget=budget)]


MAX_PARQUET_DISTINCT_DIGESTS = 10_000


@dataclass
class _ParquetColumnEvidence:
    sensitive: bool
    rows: int = 0
    non_null: int = 0
    digests: set[bytes] = field(default_factory=set, repr=False)
    overflow: bool = False
    unknown: bool = False


def _inspect_parquet_columns(
    parquet_file: Any, *, budget: LocalProfileBudget | None = None,
) -> list[_ParquetColumnEvidence]:
    """One bounded scan retains sensitivity and capped, private scalar digests."""
    observations = [_ParquetColumnEvidence(infer_sensitive_from_name(item.name))
                    for item in parquet_file.schema_arrow]
    budget = budget or LocalProfileBudget()
    expanded = 0
    total_cells = 0
    for batch in parquet_file.iter_batches(batch_size=256):
        budget.check_deadline("Parquet sensitivity inspection")
        expanded, total_cells = inspect_parquet_batch(
            batch, decoded_bytes=expanded, total_cells=total_cells,
            check_deadline=budget.check_deadline,
        )
        for index, column in enumerate(batch.columns):
            for scalar in column:
                budget.check_deadline("Parquet sensitivity inspection")
                value = scalar.as_py()
                # This representation is inspection-only, never native matching.
                evidence = str(value) if type(value) in (int, float, Decimal) else value
                # Binary/composite content is unsupported evidence, not proof of safety.
                if isinstance(value, (bytes, list, tuple, dict)) or infer_sensitive_value_type(evidence):
                    observations[index].sensitive = True
                _observe_distinct(observations[index], value)
    budget.check_deadline("Parquet sensitivity inspection")
    return observations


def _observe_distinct(evidence: _ParquetColumnEvidence, value: Any) -> None:
    evidence.rows += 1
    if value is None:
        return
    evidence.non_null += 1
    if evidence.unknown:
        return
    if isinstance(value, (bytes, list, tuple, dict)) or (
        isinstance(value, float) and not math.isfinite(value)
    ) or (isinstance(value, Decimal) and not value.is_finite()):
        evidence.unknown = True
        evidence.digests.clear()
        return
    # Arrow fixes the scalar type per field; normalize signed floating zero.
    text = "0" if isinstance(value, (float, Decimal)) and value == 0 else str(value)
    encoded = f"{type(value).__name__}:{text}".encode("utf-8")
    digest = hashlib.sha256(encoded).digest()
    if digest in evidence.digests:
        return
    if len(evidence.digests) < MAX_PARQUET_DISTINCT_DIGESTS:
        evidence.digests.add(digest)
    else:
        evidence.overflow = True


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
