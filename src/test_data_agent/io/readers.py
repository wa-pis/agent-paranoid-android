"""Read DatasetSpec-oriented inputs from disk."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from test_data_agent.core.dataset import DatasetSpec


def load_dataset_spec(path: Path) -> DatasetSpec:
    return DatasetSpec.model_validate(yaml.safe_load(path.read_text()) or {})


def load_dataset_rows(input_folder: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(input_folder.iterdir()):
        if path.suffix == ".csv":
            with path.open(newline="") as handle:
                rows_by_entity[path.stem] = [dict(row) for row in csv.DictReader(handle)]
        elif path.suffix == ".json":
            payload = json.loads(path.read_text())
            if isinstance(payload, list):
                rows_by_entity[path.stem] = payload
        elif path.suffix == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise SystemExit("Parquet input requires pyarrow") from exc
            rows_by_entity[path.stem] = pq.read_table(path).to_pylist()
    return rows_by_entity
