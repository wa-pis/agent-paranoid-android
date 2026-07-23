"""Write DatasetSpec-oriented outputs to disk."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from numbers import Number
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import (
    enforce_output_folder_size,
    enforce_output_payload_size,
)
from test_data_agent.core.settings import OutputFormat as DatasetOutputFormat


SAFE_ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def dataset_spec_to_yaml(spec: DatasetSpec) -> str:
    return yaml.safe_dump(spec.model_dump(mode="json"), sort_keys=False)


def dataset_spec_to_json(spec: DatasetSpec) -> str:
    return spec.model_dump_json(indent=2)


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def write_parquet(rows: list[dict[str, Any]], output: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit("Parquet output requires pyarrow") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        pq.write_table(pa.Table.from_pylist(parquet_rows(rows)), output)
        enforce_output_payload_size(output.stat().st_size, label=f"output file {output.name!r}")
    except Exception:
        output.unlink(missing_ok=True)
        raise


def parquet_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve homogeneous column types while supporting mixed invalid data."""
    if not rows:
        return rows
    families: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for key, value in row.items():
            if value is None:
                continue
            if isinstance(value, bool):
                family = "bool"
            elif isinstance(value, Number):
                family = "number"
            else:
                family = type(value).__name__
            families[key].add(family)
    string_columns = {key for key, types in families.items() if len(types) > 1}
    if not string_columns:
        return rows
    return [
        {
            key: None if value is None else str(value)
            if key in string_columns
            else value
            for key, value in row.items()
        }
        for row in rows
    ]


def write_dataset_rows(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    output_format: DatasetOutputFormat,
    output_folder: Path,
) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    root = output_folder.resolve(strict=True)
    for entity_name, rows in rows_by_entity.items():
        if output_format == DatasetOutputFormat.CSV:
            write_bounded_text(
                rows_to_csv(rows),
                safe_entity_artifact_path(root, entity_name, ".csv"),
            )
        elif output_format == DatasetOutputFormat.JSON:
            write_bounded_text(
                json.dumps(rows, indent=2, sort_keys=True),
                safe_entity_artifact_path(root, entity_name, ".json"),
            )
        elif output_format == DatasetOutputFormat.PARQUET:
            write_parquet(rows, safe_entity_artifact_path(root, entity_name, ".parquet"))
        enforce_output_folder_size(root)


def safe_entity_artifact_path(output_folder: Path, entity_name: str, suffix: str) -> Path:
    if not SAFE_ARTIFACT_NAME_RE.fullmatch(entity_name):
        raise ValueError(f"unsafe entity artifact name: {entity_name!r}")
    path = (output_folder / f"{entity_name}{suffix}").resolve(strict=False)
    if not path.is_relative_to(output_folder):
        raise ValueError("entity artifact path escapes output folder")
    return path


def write_bounded_text(text: str, output: Path) -> None:
    payload = text.encode("utf-8")
    enforce_output_payload_size(len(payload), label=f"output file {output.name!r}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)


def write_single_entity_rows(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    output_format: DatasetOutputFormat,
    output: Path | None,
) -> None:
    if len(rows_by_entity) != 1:
        raise SystemExit("single-entity output requires exactly one generated entity")
    rows = next(iter(rows_by_entity.values()))
    if output_format == DatasetOutputFormat.CSV:
        text = rows_to_csv(rows)
        if output is None:
            enforce_output_payload_size(len(text.encode("utf-8")), label="standard output")
            print(text)
            return
        write_bounded_text(text, output)
    elif output_format == DatasetOutputFormat.JSON:
        text = json.dumps(rows, indent=2, sort_keys=True)
        if output is None:
            enforce_output_payload_size(len(text.encode("utf-8")), label="standard output")
            print(text)
            return
        write_bounded_text(text, output)
    elif output_format == DatasetOutputFormat.PARQUET:
        if output is None:
            raise SystemExit("Parquet output requires --output")
        write_parquet(rows, output)
