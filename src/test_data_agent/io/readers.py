"""Read DatasetSpec-oriented inputs from disk."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import (
    configure_csv_field_limit,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
    enforce_parquet_metadata_limits,
    read_limited_text,
)
from test_data_agent.core.serialization import load_limited_yaml
from test_data_agent.csv_profiler import detect_csv_dialect, detect_csv_encoding, validate_csv_headers


def load_dataset_spec(path: Path) -> DatasetSpec:
    return DatasetSpec.model_validate(load_limited_yaml(read_limited_text(path)) or {})


def load_dataset_rows(input_folder: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    input_paths = [path for path in sorted(input_folder.iterdir()) if path.suffix in {".csv", ".json", ".parquet"}]
    enforce_input_files(input_paths)
    configure_csv_field_limit(csv)
    total_rows = 0
    total_cells = 0
    for path in input_paths:
        if path.suffix == ".csv":
            encoding = detect_csv_encoding(path)
            with path.open(newline="", encoding=encoding) as handle:
                sample = handle.read(8192)
                handle.seek(0)
                reader = csv.DictReader(handle, dialect=detect_csv_dialect(sample))
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
            payload = json.loads(read_limited_text(path))
            if isinstance(payload, list):
                total_rows += len(payload)
                enforce_input_row_count(total_rows, label="dataset")
                rows_by_entity[path.stem] = payload
        elif path.suffix == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise SystemExit("Parquet input requires pyarrow") from exc
            parquet_file = pq.ParquetFile(path)
            enforce_parquet_metadata_limits(parquet_file.metadata, label=f"Parquet {path.name!r}")
            total_rows += int(parquet_file.metadata.num_rows if parquet_file.metadata is not None else 0)
            enforce_input_row_count(total_rows, label="dataset")
            rows_by_entity[path.stem] = parquet_file.read().to_pylist()
    return rows_by_entity
