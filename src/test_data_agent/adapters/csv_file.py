"""CSV adapters that normalize safe CSV profiles into DatasetProfile and DatasetSpec."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.csv_profiler import CSVProfile, profile_csv
from test_data_agent.adapters.legacy_profile import (
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
)


def csv_profile_to_dataset_profile(profile: CSVProfile) -> DatasetProfile:
    return legacy_profile_to_dataset_profile(profile.model_dump(mode="json"), source_type="csv")


def csv_file_to_dataset_profile(path: Path, table_name: str | None = None) -> DatasetProfile:
    return csv_profile_to_dataset_profile(profile_csv(path, table_name=table_name))


def csv_profile_to_dataset_spec(
    profile: CSVProfile,
    *,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return legacy_profile_to_dataset_spec(
        profile.model_dump(mode="json"),
        count=count,
        seed=seed,
        source_type="csv",
    )


def csv_file_to_dataset_spec(
    path: Path,
    *,
    table_name: str | None = None,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return csv_profile_to_dataset_spec(
        profile_csv(path, table_name=table_name),
        count=count,
        seed=seed,
    )


def dataset_profile_from_csv_file(path: Path, table_name: str | None = None) -> DatasetProfile:
    return csv_file_to_dataset_profile(path, table_name=table_name)


def dataset_spec_from_csv_file(
    path: Path,
    *,
    table_name: str | None = None,
    count: int | None = None,
    seed: int | None = None,
) -> DatasetSpec:
    return csv_file_to_dataset_spec(
        path,
        table_name=table_name,
        count=count,
        seed=seed,
    )
