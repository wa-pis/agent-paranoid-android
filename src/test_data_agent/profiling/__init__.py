"""Dataset profiling pipeline."""

from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.profiling.cache import DEFAULT_PROFILE_CACHE_DIR, load_cached_profile, write_cached_profile
from test_data_agent.profiling.constraint_miner import infer_constraints
from test_data_agent.profiling.relationship_profiler import infer_relationships
from test_data_agent.profiling.schema_profiler import load_csv_folder, profile_schema

DEFAULT_RULE_SAMPLE_ROWS = 50_000


def profile_example_folder(
    input_folder: Path,
    cache_dir: Path | None = DEFAULT_PROFILE_CACHE_DIR,
    use_cache: bool = True,
    rule_sample_rows: int = DEFAULT_RULE_SAMPLE_ROWS,
) -> DatasetProfile:
    if use_cache and cache_dir is not None:
        cached = load_cached_profile(input_folder, cache_dir=cache_dir)
        if cached is not None:
            return cached

    rows_by_entity = load_csv_folder(input_folder, max_rows_per_entity=rule_sample_rows)
    profile = profile_schema(input_folder)
    profile.relationships = infer_relationships(profile, rows_by_entity)
    profile.constraints = infer_constraints(profile, rows_by_entity)
    if use_cache and cache_dir is not None:
        write_cached_profile(input_folder, profile, cache_dir=cache_dir)
    return profile


__all__ = [
    "infer_constraints",
    "infer_relationships",
    "load_csv_folder",
    "profile_example_folder",
    "profile_schema",
]
