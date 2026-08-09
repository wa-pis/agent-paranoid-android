"""Write DatasetSpec-oriented outputs to disk."""

from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import defaultdict
from numbers import Number
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from test_data_agent.core.dataset import RESERVED_ENTITY_ARTIFACT_BASENAMES, DatasetSpec
from test_data_agent.core.limits import (
    enforce_output_folder_size,
    enforce_output_payload_size,
)
from test_data_agent.core.settings import OutputFormat as DatasetOutputFormat
from test_data_agent.io.path_policy import atomic_binary_writer, atomic_write_bytes


SAFE_ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def dataset_spec_to_yaml(spec: DatasetSpec) -> str:
    return yaml.safe_dump(spec.model_dump(mode="json"), sort_keys=False)


def dataset_spec_to_json(spec: DatasetSpec) -> str:
    return spec.model_dump_json(indent=2)


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""

    handle = StringIO()
    fieldnames = list(rows[0])
    fieldname_set = set(fieldnames)
    writer = csv.writer(handle)
    writer.writerow([neutralize_csv_cell(name) for name in fieldnames])
    for row in rows:
        if set(row) - fieldname_set:
            raise ValueError("CSV rows must share one schema")
        writer.writerow([neutralize_csv_cell(row.get(name)) for name in fieldnames])
    return handle.getvalue()


def neutralize_csv_cell(value: Any) -> Any:
    """Prevent string cells from being interpreted as spreadsheet formulas."""
    if not isinstance(value, str) or not value:
        return value
    stripped = value.lstrip(" \t\r\n")
    if value[0] in "\t\r\n" or (stripped and stripped[0] in "=+-@"):
        return "'" + value
    return value


def require_safe_artifact_name(name: str) -> str:
    if (
        name in {".", ".."}
        or Path(name).name != name
        or not SAFE_ARTIFACT_NAME_RE.fullmatch(name)
    ):
        raise ValueError("unsafe artifact name")
    return name


def rows_to_sql(entity_name: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    columns = list(rows[0])
    quoted_table = quote_sql_identifier(entity_name)
    quoted_columns = ", ".join(quote_sql_identifier(column) for column in columns)
    statements = []
    for row in rows:
        values = ", ".join(sql_literal(row.get(column)) for column in columns)
        statements.append(
            f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({values});"
        )
    return "\n".join(statements) + "\n"


def quote_sql_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("SQL identifiers must be non-empty and contain no NUL bytes")
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("SQL output does not support non-finite floats")
        return repr(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def write_parquet(rows: list[dict[str, Any]], output: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ValueError(
            "Parquet output requires agent-paranoid-android[parquet]"
        ) from exc

    with atomic_binary_writer(output) as handle:
        pq.write_table(pa.Table.from_pylist(parquet_rows(rows)), handle)
        handle.flush()
        enforce_output_payload_size(
            os.fstat(handle.fileno()).st_size,
            label=f"output file {output.name!r}",
        )


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
    root = output_folder.absolute()
    if any(name in RESERVED_ENTITY_ARTIFACT_BASENAMES for name in rows_by_entity):
        raise ValueError("reserved entity name")
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
        elif output_format == DatasetOutputFormat.SQL:
            write_bounded_text(
                rows_to_sql(entity_name, rows),
                safe_entity_artifact_path(root, entity_name, ".sql"),
            )
        elif output_format == DatasetOutputFormat.PARQUET:
            write_parquet(rows, safe_entity_artifact_path(root, entity_name, ".parquet"))
        enforce_output_folder_size(root)


def safe_entity_artifact_path(output_folder: Path, entity_name: str, suffix: str) -> Path:
    try:
        require_safe_artifact_name(entity_name)
    except ValueError:
        raise ValueError(f"unsafe entity artifact name: {entity_name!r}") from None
    path = output_folder / f"{entity_name}{suffix}"
    if not path.is_relative_to(output_folder):
        raise ValueError("entity artifact path escapes output folder")
    return path


def write_bounded_text(text: str, output: Path) -> None:
    payload = text.encode("utf-8")
    enforce_output_payload_size(len(payload), label=f"output file {output.name!r}")
    atomic_write_bytes(output, payload)


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
    elif output_format == DatasetOutputFormat.SQL:
        entity_name = next(iter(rows_by_entity))
        text = rows_to_sql(entity_name, rows)
        if output is None:
            enforce_output_payload_size(len(text.encode("utf-8")), label="standard output")
            print(text, end="")
            return
        write_bounded_text(text, output)
    elif output_format == DatasetOutputFormat.PARQUET:
        if output is None:
            raise SystemExit("Parquet output requires --output")
        write_parquet(rows, output)
