"""Read DatasetSpec-oriented inputs from disk."""

from __future__ import annotations

from test_data_agent.io.csv_encoding import CSV_ENCODING, decode_csv_cell

from test_data_agent.core.csv_reader import ScopedDictReader
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec, parse_dataset_spec_payload
from test_data_agent.core.limits import (
    bounded_directory_paths,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
    enforce_parquet_metadata_limits,
    inspect_json_rows,
    read_limited_text,
)
from test_data_agent.core.parquet_limits import inspect_parquet_batch
from test_data_agent.core.serialization import load_limited_json, load_limited_yaml
from test_data_agent.csv_profiler import detect_csv_dialect, detect_csv_encoding, validate_csv_headers
from test_data_agent.migration import reject_removed_spec_payload
from test_data_agent.profiling.budget import LocalProfileBudget


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
    budget = LocalProfileBudget()
    manifest_path = input_folder / "generation_manifest.json"
    csv_encoding = None
    artifact_entities: dict[str, str] = {}
    if manifest_path.is_file():
        manifest = load_limited_json(read_limited_text(manifest_path), label="generation manifest")
        if isinstance(manifest, dict):
            csv_encoding = manifest.get("csv_encoding")
            mapping = manifest.get("entity_artifacts")
            if mapping is not None:
                if not isinstance(mapping, dict) or any(
                    not isinstance(entity, str) or not entity or not isinstance(name, str)
                    or Path(name).name != name or not name or entity in {".", ".."}
                    for entity, name in mapping.items()
                ) or len(set(mapping.values())) != len(mapping):
                    raise ValueError("invalid entity artifact mapping")
                artifact_entities = {name: entity for entity, name in mapping.items()}
        if csv_encoding is not None and csv_encoding != CSV_ENCODING:
            raise ValueError("unsupported CSV scalar encoding")
    input_paths = bounded_directory_paths(
        input_folder, (".csv", ".json", ".parquet", ".sql"),
        lambda: budget.check_deadline("dataset inventory"),
    )
    stems = [artifact_entities.get(path.name, path.stem) for path in input_paths]
    if len(stems) != len(set(stems)):
        raise ValueError("duplicate entity artifact names")
    enforce_input_files(input_paths)
    total_rows = 0
    total_cells = 0
    decoded_bytes = 0
    for path in input_paths:
        entity_name = artifact_entities.get(path.name, path.stem)
        if path.suffix == ".csv":
            encoding = detect_csv_encoding(path)
            with path.open(newline="", encoding=encoding) as handle:
                sample = handle.read(8192)
                handle.seek(0)
                reader = ScopedDictReader(handle, dialect=detect_csv_dialect(sample))
                headers = reader.fieldnames
                if csv_encoding == CSV_ENCODING and headers is not None:
                    headers = [decode_csv_cell(name) or "" for name in headers]
                fieldnames = validate_csv_headers(headers)
                enforce_input_column_count(len(fieldnames), label=f"CSV {path.name!r}")
                reader.fieldnames = fieldnames
                rows: list[dict[str, Any]] = []
                for row in reader:
                    rows.append({name: decode_csv_cell(value) for name, value in row.items()}
                                if csv_encoding == CSV_ENCODING else dict(row))
                    total_rows += 1
                    total_cells += len(fieldnames)
                    enforce_input_row_count(total_rows, label="dataset")
                    enforce_input_cell_count(total_cells, label="dataset")
                rows_by_entity[entity_name] = rows
        elif path.suffix == ".sql":
            from test_data_agent.io.sql_rows import read_insert_rows
            rows = read_insert_rows(read_limited_text(path), entity_name, budget=budget,
                                    start_rows=total_rows, start_cells=total_cells)
            total_rows += len(rows)
            total_cells += sum(len(row) for row in rows)
            rows_by_entity[entity_name] = rows
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
                rows_by_entity[entity_name] = payload
        elif path.suffix == ".parquet":
            try:
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
                decoded_bytes, total_cells = inspect_parquet_batch(
                    batch, decoded_bytes=decoded_bytes, total_cells=total_cells,
                )
                from test_data_agent.io.parquet_encoding import decode_batch_rows
                rows.extend(decode_batch_rows(batch))
            rows_by_entity[entity_name] = rows
    return rows_by_entity
