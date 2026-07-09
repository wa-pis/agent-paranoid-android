"""CSV-folder adapters that normalize safe example datasets into DatasetProfile and DatasetSpec."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.profiling import profile_example_folder


def csv_folder_to_dataset_profile(
    path: Path,
    *,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    rule_sample_rows: int | None = None,
) -> DatasetProfile:
    profile_kwargs: dict[str, object] = {
        "cache_dir": cache_dir,
        "use_cache": use_cache,
    }
    if rule_sample_rows is not None:
        profile_kwargs["rule_sample_rows"] = rule_sample_rows
    return profile_example_folder(path, **profile_kwargs)


def csv_folder_to_dataset_spec(
    path: Path,
    *,
    count: int | None = None,
    seed: int | None = None,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    rule_sample_rows: int | None = None,
) -> DatasetSpec:
    spec = infer_dataset_spec(
        csv_folder_to_dataset_profile(
            path,
            cache_dir=cache_dir,
            use_cache=use_cache,
            rule_sample_rows=rule_sample_rows,
        ),
        count=count,
    )
    if seed is not None:
        spec.generation_settings.seed = seed
    return spec


def dataset_profile_from_csv_folder(
    path: Path,
    *,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    rule_sample_rows: int | None = None,
) -> DatasetProfile:
    return csv_folder_to_dataset_profile(
        path,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )


def dataset_spec_from_csv_folder(
    path: Path,
    *,
    count: int | None = None,
    seed: int | None = None,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    rule_sample_rows: int | None = None,
) -> DatasetSpec:
    return csv_folder_to_dataset_spec(
        path,
        count=count,
        seed=seed,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )
