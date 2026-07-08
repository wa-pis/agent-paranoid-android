"""JSON adapters for DatasetProfile and DatasetSpec inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from test_data_agent.adapters.legacy_generation import (
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec


def load_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("JSON adapter expects an object payload")
    return payload


def json_payload_to_dataset_profile(payload: dict[str, Any]) -> DatasetProfile:
    if "entities" in payload:
        return DatasetProfile.model_validate(payload)
    if "columns" in payload:
        source_type = str(payload.get("source_type", "json_profile"))
        return legacy_profile_to_dataset_profile(payload, source_type=source_type)
    raise ValueError("JSON payload does not match DatasetProfile or legacy profile shape")


def json_payload_to_dataset_spec(
    payload: dict[str, Any],
    *,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    if "privacy_rules" in payload or "generation_settings" in payload or "validation_settings" in payload:
        spec = DatasetSpec.model_validate(payload)
        if count is not None:
            for entity in spec.entities:
                entity.row_count = count
        if seed is not None:
            spec.generation_settings.seed = seed
        return spec
    if "entities" in payload:
        return legacy_profile_to_dataset_spec(
            DatasetProfile.model_validate(payload).model_dump(mode="json"),
            count=count,
            seed=seed,
            source_type=str(payload.get("source_type", "json_profile")),
        )
    if "columns" in payload:
        source_type = str(payload.get("source_type", "json_profile"))
        return legacy_profile_to_dataset_spec(payload, count=count, seed=seed, source_type=source_type)
    raise ValueError("JSON payload does not match DatasetSpec, DatasetProfile, or legacy profile shape")


def load_json_dataset_profile(path: Path) -> DatasetProfile:
    return json_payload_to_dataset_profile(load_json_payload(path))


def load_json_dataset_spec(
    path: Path,
    *,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return json_payload_to_dataset_spec(load_json_payload(path), count=count, seed=seed)
