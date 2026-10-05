"""Shared Arrow inspection before conversion to Python values."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from test_data_agent.core.limits import (
    InputLimitError, enforce_input_cell_count, max_input_cell_chars,
    max_json_depth, max_parquet_expanded_bytes,
)


def inspect_parquet_batch(
    batch: Any, *, decoded_bytes: int, total_cells: int,
    check_deadline: Callable[[str], None] | None = None,
) -> tuple[int, int]:
    import pyarrow as pa
    import pyarrow.compute as pc

    decoded_bytes += batch.nbytes
    _enforce_decoded_bytes(decoded_bytes)
    for column in batch.columns:
        for scalar in column:
            for value, dictionary in _parquet_leaf_values(scalar):
                if check_deadline is not None:
                    check_deadline("Parquet logical inspection")
                total_cells += 1
                enforce_input_cell_count(total_cells, label="dataset")
                if value.is_valid and hasattr(value, "as_buffer"):
                    size = value.as_buffer().size
                    if dictionary:
                        decoded_bytes += size + 8
                        _enforce_decoded_bytes(decoded_bytes)
                    length = pc.utf8_length(value).as_py() if (
                        pa.types.is_string(value.type) or pa.types.is_large_string(value.type)
                    ) else size
                    if length > max_input_cell_chars():
                        raise InputLimitError("Parquet cell exceeds configured size limit")
                elif dictionary and value.is_valid:
                    decoded_bytes += max(1, getattr(value.type, "bit_width", 64) // 8)
                    _enforce_decoded_bytes(decoded_bytes)
    return decoded_bytes, total_cells


def _enforce_decoded_bytes(size: int) -> None:
    if size > max_parquet_expanded_bytes():
        raise InputLimitError("dataset Parquet decoded size exceeds configured byte limit")


def _parquet_leaf_values(
    value: Any, *, depth: int = 1, dictionary: bool = False,
) -> Iterator[tuple[Any, bool]]:
    """Walk Arrow scalars without materializing nested Python containers."""
    import pyarrow as pa
    if depth > max_json_depth():
        raise InputLimitError("Parquet cell exceeds configured nesting limit")
    if not value.is_valid:
        yield value, dictionary
    elif pa.types.is_dictionary(value.type):
        yield from _parquet_leaf_values(value.value, depth=depth, dictionary=True)
    elif pa.types.is_struct(value.type):
        for child in value.values():
            yield from _parquet_leaf_values(child, depth=depth + 1, dictionary=dictionary)
    elif (pa.types.is_list(value.type) or pa.types.is_large_list(value.type)
          or pa.types.is_fixed_size_list(value.type) or pa.types.is_map(value.type)):
        for child in value.values:
            yield from _parquet_leaf_values(child, depth=depth + 1, dictionary=dictionary)
    elif pa.types.is_union(value.type) or isinstance(value.type, pa.ExtensionType):
        raise InputLimitError("unsupported Parquet cell type")
    else:
        yield value, dictionary
