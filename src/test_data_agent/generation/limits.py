"""Allocation estimates shared by deterministic generation and I/O preflight."""

import json
from typing import Any

from test_data_agent.core.dataset import DatasetSpec


def estimate_dataset_output_bytes(spec: DatasetSpec) -> int:
    total = len(spec.model_dump_json().encode("utf-8")) * 2 + 65_536
    for entity in spec.entities:
        row_bytes = 2
        for field in entity.fields:
            row_bytes += len(field.name.encode("utf-8")) + estimate_field_output_bytes(field) + 8
        total += entity.row_count * row_bytes * 2
    return total


def estimate_field_output_bytes(field: Any) -> int:
    if field.is_identifier:
        return len(field.name.encode("utf-8")) + 64
    if field.sensitive:
        return 128
    if field.data_type != "string":
        return 64
    distribution = field.distribution or {}
    if distribution.get("kind") == "categorical":
        categories = distribution.get("categories") or []
        return max(
            (
                len(json.dumps(category.get("value"), default=str).encode("utf-8"))
                for category in categories
            ),
            default=16,
        )
    maximum = int(distribution.get("max_length", 12))
    return max(1, maximum) + 4

