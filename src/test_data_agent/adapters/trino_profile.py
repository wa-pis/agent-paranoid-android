"""Adapters for safe Trino profile metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from test_data_agent.adapters.legacy_generation import (
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec


def trino_profile_to_dataset_profile(profile: Mapping[str, Any]) -> DatasetProfile:
    return legacy_profile_to_dataset_profile(profile, source_type="trino")


def trino_profile_to_dataset_spec(
    profile: Mapping[str, Any],
    *,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return legacy_profile_to_dataset_spec(
        profile,
        count=count,
        seed=seed,
        source_type="trino",
    )


def dataset_profile_from_trino_profile(profile: Mapping[str, Any]) -> DatasetProfile:
    return trino_profile_to_dataset_profile(profile)


def dataset_spec_from_trino_profile(
    profile: Mapping[str, Any],
    *,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return trino_profile_to_dataset_spec(profile, count=count, seed=seed)
