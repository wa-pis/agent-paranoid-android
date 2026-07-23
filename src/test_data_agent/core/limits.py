"""Shared resource limits for synthetic data generation."""

from __future__ import annotations

import os
import shutil
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable


MAX_GENERATION_COUNT_ENV = "TEST_DATA_AGENT_MAX_GENERATION_COUNT"
DEFAULT_MAX_GENERATION_COUNT = 100_000
MAX_INPUT_FILE_BYTES_ENV = "TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES"
MAX_TOTAL_INPUT_BYTES_ENV = "TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES"
MAX_INPUT_ROWS_ENV = "TEST_DATA_AGENT_MAX_INPUT_ROWS"
MAX_INPUT_COLUMNS_ENV = "TEST_DATA_AGENT_MAX_INPUT_COLUMNS"
MAX_INPUT_CELLS_ENV = "TEST_DATA_AGENT_MAX_INPUT_CELLS"
MAX_INPUT_FILES_ENV = "TEST_DATA_AGENT_MAX_INPUT_FILES"
MAX_INPUT_CELL_CHARS_ENV = "TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS"
MAX_PARQUET_EXPANDED_BYTES_ENV = "TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES"
MAX_YAML_ALIASES_ENV = "TEST_DATA_AGENT_MAX_YAML_ALIASES"
MAX_YAML_DEPTH_ENV = "TEST_DATA_AGENT_MAX_YAML_DEPTH"
MAX_BUSINESS_RULES_BYTES_ENV = "TEST_DATA_AGENT_MAX_BUSINESS_RULES_BYTES"
MAX_BUSINESS_RULE_EVALUATIONS_ENV = "TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS"
MAX_OUTPUT_BYTES_ENV = "TEST_DATA_AGENT_MAX_OUTPUT_BYTES"
MIN_FREE_DISK_BYTES_ENV = "TEST_DATA_AGENT_MIN_FREE_DISK_BYTES"
MAX_GENERATION_SECONDS_ENV = "TEST_DATA_AGENT_MAX_GENERATION_SECONDS"

DEFAULT_MAX_INPUT_FILE_BYTES = 128 * 1024 * 1024
DEFAULT_MAX_TOTAL_INPUT_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_INPUT_ROWS = 1_000_000
DEFAULT_MAX_INPUT_COLUMNS = 1_000
DEFAULT_MAX_INPUT_CELLS = 10_000_000
DEFAULT_MAX_INPUT_FILES = 100
DEFAULT_MAX_INPUT_CELL_CHARS = 1_000_000
DEFAULT_MAX_PARQUET_EXPANDED_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_YAML_ALIASES = 50
DEFAULT_MAX_YAML_DEPTH = 100
DEFAULT_MAX_BUSINESS_RULES_BYTES = 1024 * 1024
DEFAULT_MAX_BUSINESS_RULE_EVALUATIONS = 5_000_000
DEFAULT_MAX_OUTPUT_BYTES = 512 * 1024 * 1024
DEFAULT_MIN_FREE_DISK_BYTES = 128 * 1024 * 1024
DEFAULT_MAX_GENERATION_SECONDS = 300.0


class InputLimitError(ValueError):
    """Raised before an input can consume excessive local resources."""


class GenerationLimitError(ValueError):
    """Raised before generated output can exceed local resource budgets."""


class GenerationBudget:
    """Wall-clock budget checked at deterministic workflow boundaries."""

    def __init__(
        self,
        max_seconds: float | None = None,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.max_seconds = max_generation_seconds() if max_seconds is None else max_seconds
        if not self.max_seconds > 0 or self.max_seconds == float("inf"):
            raise ValueError("generation time budget must be a finite positive number")
        self._clock = clock or time.monotonic
        self._started_at = self._clock()

    def check(self, stage: str) -> None:
        if self._clock() - self._started_at > self.max_seconds:
            raise GenerationLimitError(
                f"generation exceeded the {self.max_seconds:g} second budget during {stage}"
            )


def max_generation_count() -> int:
    return positive_int_env(MAX_GENERATION_COUNT_ENV, DEFAULT_MAX_GENERATION_COUNT)


def max_input_file_bytes() -> int:
    return positive_int_env(MAX_INPUT_FILE_BYTES_ENV, DEFAULT_MAX_INPUT_FILE_BYTES)


def max_total_input_bytes() -> int:
    return positive_int_env(MAX_TOTAL_INPUT_BYTES_ENV, DEFAULT_MAX_TOTAL_INPUT_BYTES)


def max_input_rows() -> int:
    return positive_int_env(MAX_INPUT_ROWS_ENV, DEFAULT_MAX_INPUT_ROWS)


def max_input_columns() -> int:
    return positive_int_env(MAX_INPUT_COLUMNS_ENV, DEFAULT_MAX_INPUT_COLUMNS)


def max_input_cells() -> int:
    return positive_int_env(MAX_INPUT_CELLS_ENV, DEFAULT_MAX_INPUT_CELLS)


def max_input_files() -> int:
    return positive_int_env(MAX_INPUT_FILES_ENV, DEFAULT_MAX_INPUT_FILES)


def max_input_cell_chars() -> int:
    return positive_int_env(MAX_INPUT_CELL_CHARS_ENV, DEFAULT_MAX_INPUT_CELL_CHARS)


def max_parquet_expanded_bytes() -> int:
    return positive_int_env(MAX_PARQUET_EXPANDED_BYTES_ENV, DEFAULT_MAX_PARQUET_EXPANDED_BYTES)


def max_yaml_aliases() -> int:
    return positive_int_env(MAX_YAML_ALIASES_ENV, DEFAULT_MAX_YAML_ALIASES)


def max_yaml_depth() -> int:
    return positive_int_env(MAX_YAML_DEPTH_ENV, DEFAULT_MAX_YAML_DEPTH)


def max_business_rules_bytes() -> int:
    return positive_int_env(
        MAX_BUSINESS_RULES_BYTES_ENV,
        DEFAULT_MAX_BUSINESS_RULES_BYTES,
    )


def max_business_rule_evaluations() -> int:
    return positive_int_env(
        MAX_BUSINESS_RULE_EVALUATIONS_ENV,
        DEFAULT_MAX_BUSINESS_RULE_EVALUATIONS,
    )


def max_output_bytes() -> int:
    return positive_int_env(MAX_OUTPUT_BYTES_ENV, DEFAULT_MAX_OUTPUT_BYTES)


def min_free_disk_bytes() -> int:
    return positive_int_env(MIN_FREE_DISK_BYTES_ENV, DEFAULT_MIN_FREE_DISK_BYTES)


def max_generation_seconds() -> float:
    return positive_float_env(MAX_GENERATION_SECONDS_ENV, DEFAULT_MAX_GENERATION_SECONDS)


def positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def positive_float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not value > 0 or value == float("inf"):
        raise ValueError(f"{name} must be a finite positive number")
    return value


def enforce_row_count_limit(row_count: int, *, max_count: int | None = None) -> None:
    effective_max = max_generation_count() if max_count is None else max_count
    if row_count > effective_max:
        raise ValueError(f"row_count must be <= {effective_max}")


def enforce_input_files(paths: Iterable[Path]) -> list[Path]:
    resolved_paths = list(paths)
    file_limit = max_input_files()
    if len(resolved_paths) > file_limit:
        raise InputLimitError(f"input contains more than {file_limit} files")
    total_size = 0
    for path in resolved_paths:
        if path.is_symlink():
            raise InputLimitError(f"symbolic link inputs are not allowed: {path.name!r}")
        stat = path.stat()
        if not path.is_file():
            raise InputLimitError(f"input path must be a regular file: {path.name!r}")
        size = stat.st_size
        enforce_input_file_size(path, size=size)
        total_size += size
    total_limit = max_total_input_bytes()
    if total_size > total_limit:
        raise InputLimitError(f"total input size must be <= {total_limit} bytes")
    return resolved_paths


def enforce_input_file_size(path: Path, *, size: int | None = None) -> None:
    actual_size = path.stat().st_size if size is None else size
    limit = max_input_file_bytes()
    if actual_size > limit:
        raise InputLimitError(f"input file {path.name!r} must be <= {limit} bytes")


def enforce_input_row_count(row_count: int, *, label: str = "input") -> None:
    limit = max_input_rows()
    if row_count > limit:
        raise InputLimitError(f"{label} must contain <= {limit} rows")


def enforce_input_column_count(column_count: int, *, label: str = "input") -> None:
    limit = max_input_columns()
    if column_count > limit:
        raise InputLimitError(f"{label} must contain <= {limit} columns")


def enforce_input_cell_count(cell_count: int, *, label: str = "input") -> None:
    limit = max_input_cells()
    if cell_count > limit:
        raise InputLimitError(f"{label} must contain <= {limit} cells")


def configure_csv_field_limit(csv_module: Any) -> None:
    csv_module.field_size_limit(max_input_cell_chars())


def read_limited_text(
    path: Path,
    *,
    encoding: str = "utf-8",
    max_bytes: int | None = None,
) -> str:
    enforce_input_files([path])
    limit = max_input_file_bytes() if max_bytes is None else min(max_input_file_bytes(), max_bytes)
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise InputLimitError(f"input file {path.name!r} must be <= {limit} bytes")
    return payload.decode(encoding)


def enforce_business_rules_payload_size(size: int) -> None:
    limit = max_business_rules_bytes()
    if size > limit:
        raise InputLimitError(f"business rules payload must be <= {limit} bytes")


def enforce_business_rule_evaluations(count: int) -> None:
    limit = max_business_rule_evaluations()
    if count > limit:
        raise InputLimitError(
            f"business rules require more than {limit} estimated evaluations"
        )


def enforce_parquet_metadata_limits(metadata: Any, *, label: str) -> None:
    if metadata is None:
        return
    enforce_input_row_count(int(metadata.num_rows), label=label)
    enforce_input_column_count(int(metadata.num_columns), label=label)
    enforce_input_cell_count(int(metadata.num_rows) * int(metadata.num_columns), label=label)
    expanded_size = sum(
        int(metadata.row_group(row_group).column(column).total_uncompressed_size)
        for row_group in range(metadata.num_row_groups)
        for column in range(metadata.num_columns)
    )
    expanded_limit = max_parquet_expanded_bytes()
    if expanded_size > expanded_limit:
        raise InputLimitError(f"{label} expanded size must be <= {expanded_limit} bytes")


def enforce_output_capacity(path: Path) -> None:
    """Reserve room for one maximum-sized bundle plus the configured floor."""
    existing = path
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    available = shutil.disk_usage(existing).free
    required = max_output_bytes() + min_free_disk_bytes()
    if available < required:
        raise GenerationLimitError(
            f"output filesystem must have at least {required} free bytes before generation"
        )


def enforce_output_payload_size(size: int, *, label: str = "output") -> None:
    limit = max_output_bytes()
    if size > limit:
        raise GenerationLimitError(f"{label} must be <= {limit} bytes")


def output_folder_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for child in path.rglob("*"):
        if child.is_symlink():
            raise GenerationLimitError(f"symbolic links are not allowed in generated output: {child.name!r}")
        if child.is_file():
            total += child.stat().st_size
    return total


def enforce_output_folder_size(path: Path) -> None:
    enforce_output_payload_size(output_folder_size(path), label="generated artifact bundle")
