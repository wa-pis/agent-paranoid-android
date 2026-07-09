"""Compatibility re-exports for deprecated GenerationSpec helpers."""

from test_data_agent.adapters.legacy_generation import (
    LegacyGenerationResult,
    apply_legacy_mode_options,
    dataset_spec_from_generation_spec,
    dataset_spec_to_generation_spec,
    generate_legacy_compatibility_result,
    generate_legacy_rows,
    generation_spec_to_dataset_spec,
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
    legacy_profile_to_generation_spec,
    load_legacy_generation_spec,
    multi_table_generation_spec_to_dataset_spec,
    prepare_legacy_generation_spec,
    validate_legacy_rows_file,
    validate_legacy_rows_report,
)

__all__ = [
    "LegacyGenerationResult",
    "apply_legacy_mode_options",
    "dataset_spec_from_generation_spec",
    "dataset_spec_to_generation_spec",
    "generate_legacy_compatibility_result",
    "generate_legacy_rows",
    "generation_spec_to_dataset_spec",
    "legacy_profile_to_dataset_profile",
    "legacy_profile_to_dataset_spec",
    "legacy_profile_to_generation_spec",
    "load_legacy_generation_spec",
    "multi_table_generation_spec_to_dataset_spec",
    "prepare_legacy_generation_spec",
    "validate_legacy_rows_file",
    "validate_legacy_rows_report",
]
