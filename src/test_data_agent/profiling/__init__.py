"""Dataset profiling pipeline."""

from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.profiling.cache import DEFAULT_PROFILE_CACHE_DIR, load_cached_profile, write_cached_profile
from test_data_agent.profiling.budget import (
    LocalProfileBudget,
    LocalProfileDimension,
    LocalProfileLimitError,
    LocalProfileLimits,
)
from test_data_agent.profiling.constraint_miner import infer_constraints
from test_data_agent.profiling.relationship_profiler import infer_relationships
from test_data_agent.profiling.schema_profiler import (
    _profile_schema_with_sample,
    _sanitize_source_categories,
    load_csv_folder,
    profile_schema,
)

DEFAULT_RULE_SAMPLE_ROWS = 50_000


def profile_example_folder(
    input_folder: Path,
    cache_dir: Path | None = DEFAULT_PROFILE_CACHE_DIR,
    use_cache: bool = True,
    rule_sample_rows: int = DEFAULT_RULE_SAMPLE_ROWS,
    budget: LocalProfileBudget | None = None,
    local_category_fields: tuple[LocalCategoryField, ...] = (),
) -> DatasetProfile:
    work_budget = budget or LocalProfileBudget()
    work_budget.check_sample_rows(rule_sample_rows)
    work_budget.check_input_files(sorted(input_folder.glob("*.csv")))
    work_budget.check_deadline("cache lookup")
    if use_cache and cache_dir is not None:
        cached = load_cached_profile(
            input_folder,
            cache_dir=cache_dir,
            rule_sample_rows=rule_sample_rows,
        )
        if cached is not None:
            work_budget.check_deadline("cache load")
            cached.local_category_fields = list(local_category_fields)
            return cached

    profile, rows_by_entity = _profile_schema_with_sample(
        input_folder,
        max_rows_per_entity=rule_sample_rows,
        budget=work_budget,
    )
    work_budget.check_deadline("relationship inference")
    profile.relationships = infer_relationships(profile, rows_by_entity)
    work_budget.check_deadline("constraint inference")
    profile.constraints = infer_constraints(profile, rows_by_entity)
    profile = _sanitize_source_categories(profile, local_category_fields=local_category_fields)
    profile.local_category_fields = list(local_category_fields)
    work_budget.check_deadline("cache publication")
    if use_cache and cache_dir is not None:
        write_cached_profile(
            input_folder,
            profile,
            cache_dir=cache_dir,
            rule_sample_rows=rule_sample_rows,
        )
    return profile


__all__ = [
    "infer_constraints",
    "infer_relationships",
    "load_csv_folder",
    "LocalProfileBudget",
    "LocalProfileDimension",
    "LocalProfileLimitError",
    "LocalProfileLimits",
    "profile_example_folder",
    "profile_schema",
]
