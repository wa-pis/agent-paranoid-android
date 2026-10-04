"""Read DatasetSpec-oriented inputs from disk."""

from __future__ import annotations

from test_data_agent.core.csv_reader import ScopedDictReader
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec, parse_dataset_spec_payload
from test_data_agent.core.limits import (
    InputLimitError,
    max_input_cell_chars,
    max_json_depth,
    max_parquet_expanded_bytes,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
    enforce_parquet_metadata_limits,
    inspect_json_rows,
    read_limited_text,
)
from test_data_agent.core.serialization import load_limited_json, load_limited_yaml
from test_data_agent.csv_profiler import detect_csv_dialect, detect_csv_encoding, validate_csv_headers
from test_data_agent.migration import reject_removed_spec_payload


def load_dataset_spec(path: Path) -> DatasetSpec:
    payload = load_limited_yaml(read_limited_text(path)) or {}
    reject_removed_spec_payload(payload)
    if _is_dataset_profile_payload(payload):
        raise ValueError(
            "expected a DatasetSpec, received a DatasetProfile; "
            "use 'generate --profile' or convert it with 'infer-spec'"
        )
    return parse_dataset_spec_payload(payload)


def _is_dataset_profile_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if "source_type" in payload:
        return True
    entities = payload.get("entities")
    if not isinstance(entities, list):
        return False
    return any(
        isinstance(entity, dict) and "primary_key_candidates" in entity
        for entity in entities
    )


def load_dataset_rows(input_folder: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    input_paths = [path for path in sorted(input_folder.iterdir()) if path.suffix in {".csv", ".json", ".parquet"}]
    stems = [path.stem for path in input_paths]
    if len(stems) != len(set(stems)):
        raise ValueError("duplicate entity artifact names")
    enforce_input_files(input_paths)
    total_rows = 0
    total_cells = 0
    decoded_bytes = 0
    for path in input_paths:
        if path.suffix == ".csv":
            encoding = detect_csv_encoding(path)
            with path.open(newline="", encoding=encoding) as handle:
                sample = handle.read(8192)
                handle.seek(0)
                reader = ScopedDictReader(handle, dialect=detect_csv_dialect(sample))
                fieldnames = validate_csv_headers(reader.fieldnames)
                enforce_input_column_count(len(fieldnames), label=f"CSV {path.name!r}")
                reader.fieldnames = fieldnames
                rows: list[dict[str, Any]] = []
                for row in reader:
                    rows.append(dict(row))
                    total_rows += 1
                    total_cells += len(fieldnames)
                    enforce_input_row_count(total_rows, label="dataset")
                    enforce_input_cell_count(total_cells, label="dataset")
                rows_by_entity[path.stem] = rows
        elif path.suffix == ".json":
            payload = load_limited_json(
                read_limited_text(path),
                label=f"JSON {path.name!r}",
            )
            if isinstance(payload, list):
                row_count, cell_count = inspect_json_rows(
                    payload,
                    label=f"JSON {path.name!r}",
                )
                total_rows += row_count
                total_cells += cell_count
                enforce_input_row_count(total_rows, label="dataset")
                enforce_input_cell_count(total_cells, label="dataset")
                rows_by_entity[path.stem] = payload
        elif path.suffix == ".parquet":
            try:
                import pyarrow as pa
                import pyarrow.compute as pc
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise ValueError(
                    "Parquet input requires agent-paranoid-android[parquet]"
                ) from exc
            parquet_file = pq.ParquetFile(path)
            enforce_parquet_metadata_limits(parquet_file.metadata, label=f"Parquet {path.name!r}")
            rows = []
            for batch in parquet_file.iter_batches(batch_size=256):
                total_rows += batch.num_rows
                enforce_input_row_count(total_rows, label="dataset")
                # Arrow allocates a batch before this check; reject before Python rows.
                decoded_bytes += batch.nbytes
                _enforce_decoded_bytes(decoded_bytes)
                for column in batch.columns:
                    for scalar in column:
                        for value, dictionary in _parquet_leaf_values(scalar):
                            total_cells += 1
                            enforce_input_cell_count(total_cells, label="dataset")
                            if value.is_valid and hasattr(value, "as_buffer"):
                                size = value.as_buffer().size
                                if dictionary:
                                    # Retained dictionaries need an additional logical-expansion bound.
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
                rows.extend(batch.to_pylist())
            rows_by_entity[path.stem] = rows
    return rows_by_entity


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
