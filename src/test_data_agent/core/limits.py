"""Shared resource limits for synthetic data generation."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any


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


class InputLimitError(ValueError):
    """Raised before an input can consume excessive local resources."""


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


def read_limited_text(path: Path, *, encoding: str = "utf-8") -> str:
    enforce_input_files([path])
    limit = max_input_file_bytes()
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise InputLimitError(f"input file {path.name!r} must be <= {limit} bytes")
    return payload.decode(encoding)


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
