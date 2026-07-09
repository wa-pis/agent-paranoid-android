"""Write DatasetSpec-oriented outputs to disk."""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat as DatasetOutputFormat
from test_data_agent.spec import GenerationSpec


def dataset_spec_to_yaml(spec: DatasetSpec) -> str:
    return yaml.safe_dump(spec.model_dump(mode="json"), sort_keys=False)


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
    stable_rows = [
        {key: None if value is None else str(value) for key, value in row.items()}
        for row in rows
    ]
    pq.write_table(pa.Table.from_pylist(stable_rows), output)


def write_tabular_rows(rows: list[dict[str, Any]], spec: GenerationSpec, output: Path | None) -> None:
    if spec.output_format == "parquet":
        if output is None:
            raise SystemExit("Parquet output requires --output")
        write_parquet(rows, output)
        return

    if spec.output_format == "csv":
        text = rows_to_csv(rows)
    else:
        text = json.dumps(rows, indent=2, sort_keys=True)

    if output is None:
        print(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)


def write_dataset_rows(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    output_format: DatasetOutputFormat,
    output_folder: Path,
) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    for entity_name, rows in rows_by_entity.items():
        if output_format == DatasetOutputFormat.CSV:
            (output_folder / f"{entity_name}.csv").write_text(rows_to_csv(rows))
        elif output_format == DatasetOutputFormat.JSON:
            (output_folder / f"{entity_name}.json").write_text(json.dumps(rows, indent=2, sort_keys=True))
        elif output_format == DatasetOutputFormat.PARQUET:
            write_parquet(rows, output_folder / f"{entity_name}.parquet")


def write_single_entity_rows(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    output_format: DatasetOutputFormat,
    output: Path,
) -> None:
    if len(rows_by_entity) != 1:
        raise SystemExit("single-entity output requires exactly one generated entity")
    rows = next(iter(rows_by_entity.values()))
    if output_format == DatasetOutputFormat.CSV:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rows_to_csv(rows))
    elif output_format == DatasetOutputFormat.JSON:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2, sort_keys=True))
    elif output_format == DatasetOutputFormat.PARQUET:
        write_parquet(rows, output)
