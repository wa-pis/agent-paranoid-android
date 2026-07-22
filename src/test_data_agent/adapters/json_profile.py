"""JSON adapters for DatasetProfile and DatasetSpec inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from test_data_agent.adapters.legacy_profile import (
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.generation.planner import infer_dataset_spec


def load_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(read_limited_text(path))
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
    if (
        "schema_version" in payload
        or "privacy_rules" in payload
        or "privacy_settings" in payload
        or "generation_settings" in payload
        or "validation_settings" in payload
    ):
        spec = DatasetSpec.model_validate(payload)
        if count is not None:
            for entity in spec.entities:
                entity.row_count = count
        if seed is not None:
            spec.generation_settings.seed = seed
        return spec
    if "entities" in payload:
        first_entity = payload["entities"][0] if payload["entities"] else {}
        if isinstance(first_entity, dict) and "primary_key_candidates" in first_entity:
            spec = infer_dataset_spec(DatasetProfile.model_validate(payload), count=count)
        else:
            spec = DatasetSpec.model_validate(payload)
            if count is not None:
                for entity in spec.entities:
                    entity.row_count = count
        if seed is not None:
            spec.generation_settings.seed = seed
        return spec
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


def load_profile_or_spec(path: Path) -> DatasetProfile | DatasetSpec:
    payload = load_json_payload(path)
    if (
        "schema_version" in payload
        or "privacy_rules" in payload
        or "privacy_settings" in payload
        or "generation_settings" in payload
        or "validation_settings" in payload
    ):
        return DatasetSpec.model_validate(payload)
    if "columns" in payload:
        return json_payload_to_dataset_profile(payload)
    if "source_type" in payload:
        try:
            return DatasetProfile.model_validate(payload)
        except ValidationError:
            if "columns" in payload:
                return json_payload_to_dataset_profile(payload)
            raise
    if "entities" in payload:
        first_entity = payload["entities"][0] if payload["entities"] else {}
        if isinstance(first_entity, dict) and "primary_key_candidates" in first_entity:
            return DatasetProfile.model_validate(payload)
        return DatasetSpec.model_validate(payload)
    return json_payload_to_dataset_profile(payload)
