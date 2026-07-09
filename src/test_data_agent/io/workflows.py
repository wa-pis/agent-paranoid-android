"""Workflow helpers for DatasetSpec-oriented CLI commands."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Callable

from test_data_agent.adapters import (
    csv_file_to_dataset_profile,
    generate_legacy_compatibility_result,
    validate_legacy_rows_file,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io.artifacts import (
    write_dataset_generation_artifacts,
    write_dataset_profile_artifact,
    write_dataset_review_artifacts,
    write_dataset_spec_artifact,
    write_dataset_validation_report,
    write_generation_artifacts,
)
from test_data_agent.io.writers import write_dataset_rows, write_single_entity_rows, write_tabular_rows
from test_data_agent.validation import DatasetValidationReport, validate_dataset


BusinessRulesApplier = Callable[[dict[str, list[dict[str, Any]]], int], Any | None]


def generate_dataset_artifacts(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
) -> int:
    effective_output_format = output_format or spec.generation_settings.output_format
    if count is not None:
        for entity in spec.entities:
            entity.row_count = count
    effective_seed = spec.generation_settings.seed if seed is None else seed
    rows_by_entity = generate_dataset(spec, seed=effective_seed or 0)
    write_dataset_rows(rows_by_entity, effective_output_format, output_folder)
    report = validate_dataset(rows_by_entity, spec)
    write_dataset_validation_report(report, output_folder)
    return 0 if report.valid else 1


def warn_deprecated_generation_spec_compatibility(command: str) -> None:
    print(
        f"warning: '{command}' is using deprecated GenerationSpec compatibility; prefer DatasetSpec inputs",
        file=sys.stderr,
    )


def build_dataset_spec_from_profile(
    profile: DatasetProfile,
    *,
    count: int,
    seed: int,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
) -> DatasetSpec:
    if len(profile.entities) != 1:
        raise ValueError("--profile generation currently requires exactly one entity profile")

    spec = infer_dataset_spec(profile, count=count)
    spec.generation_settings.seed = seed
    if output_format is not None:
        spec.generation_settings.output_format = output_format
    apply_dataset_mode_options(spec, mode=mode, invalid_ratio=invalid_ratio)
    return spec


def infer_dataset_spec_artifact(
    profile: DatasetProfile,
    *,
    output_path: Path,
    count: int | None = None,
) -> DatasetSpec:
    spec = infer_dataset_spec(profile, count=count)
    write_dataset_spec_artifact(spec, output_path)
    return spec


def write_csv_profile_artifact(
    input_path: Path,
    *,
    output_path: Path,
    table_name: str | None = None,
) -> DatasetProfile:
    profile = csv_file_to_dataset_profile(input_path, table_name=table_name)
    write_dataset_profile_artifact(profile, output_path)
    return profile


def generate_single_entity_profile_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    output_path: Path,
    rows_by_entity: dict[str, list[dict[str, Any]]] | None = None,
    business_report: Any | None = None,
    profile_artifact_name: str = "profile.json",
) -> DatasetValidationReport:
    rows_by_entity = rows_by_entity or generate_dataset(spec, seed=spec.generation_settings.seed or 0)
    write_single_entity_rows(rows_by_entity, spec.generation_settings.output_format, output_path)
    report = validate_dataset(rows_by_entity, spec)
    write_dataset_generation_artifacts(
        profile,
        spec,
        report,
        output_path,
        business_report=business_report,
        profile_artifact_name=profile_artifact_name,
    )
    return report


def generate_dataset_from_profile_artifacts(
    profile: DatasetProfile,
    *,
    count: int,
    seed: int,
    output_path: Path,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
    business_rules_applier: BusinessRulesApplier | None = None,
    profile_artifact_name: str = "profile.json",
) -> tuple[DatasetValidationReport, Any | None]:
    spec = build_dataset_spec_from_profile(
        profile,
        count=count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    rows_by_entity = generate_dataset(spec, seed=spec.generation_settings.seed or 0)
    business_report = None
    if business_rules_applier is not None:
        business_report = business_rules_applier(rows_by_entity, spec.generation_settings.seed or 0)
    report = generate_single_entity_profile_artifacts(
        profile,
        spec,
        output_path=output_path,
        rows_by_entity=rows_by_entity,
        business_report=business_report,
        profile_artifact_name=profile_artifact_name,
    )
    return report, business_report


def generate_dataset_from_csv_artifacts(
    input_path: Path,
    *,
    count: int,
    seed: int,
    output_path: Path,
    output_format: OutputFormat,
    table_name: str | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> tuple[DatasetValidationReport, Any | None]:
    profile = csv_file_to_dataset_profile(input_path, table_name=table_name)
    spec = build_dataset_spec_from_profile(
        profile,
        count=count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    rows_by_entity = generate_dataset(spec, seed=seed)
    business_report = None
    if business_rules_applier is not None:
        business_report = business_rules_applier(rows_by_entity, seed)
    report = validate_dataset(rows_by_entity, spec)
    write_single_entity_rows(rows_by_entity, output_format, output_path)
    write_dataset_generation_artifacts(profile, spec, report, output_path, business_report=business_report)
    return report, business_report


def generate_dataset_review_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat,
    seed: int,
) -> int:
    rows_by_entity = generate_dataset(spec, seed=seed)
    write_dataset_rows(rows_by_entity, output_format, output_folder)
    report = validate_dataset(rows_by_entity, spec)

    write_dataset_review_artifacts(profile, spec, report, output_folder)
    return 0 if report.valid else 1


def generate_legacy_spec_artifacts(
    spec_path: Path,
    *,
    row_count: int | None = None,
    seed: int | None = None,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
    output_path: Path | None = None,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> tuple[Any, Any | None]:
    legacy_result = generate_legacy_compatibility_result(
        spec_path,
        row_count=row_count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    apply_dataset_mode_options(
        legacy_result.dataset_spec,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    business_report = None
    if business_rules_applier is not None:
        business_report = business_rules_applier(
            {legacy_result.spec.table.name: legacy_result.rows},
            legacy_result.spec.seed or 0,
        )
    write_tabular_rows(legacy_result.rows, legacy_result.spec, output_path)
    write_generation_artifacts(
        legacy_result.spec,
        legacy_result.report,
        output_path,
        business_report=business_report,
    )
    return legacy_result, business_report


def validate_legacy_spec_artifacts(spec_path: Path, rows_path: Path) -> Any:
    return validate_legacy_rows_file(spec_path, rows_path)


def apply_dataset_mode_options(spec: DatasetSpec, *, mode: str, invalid_ratio: float) -> None:
    if mode in {"mixed", "negative"}:
        if not 0.0 <= invalid_ratio <= 1.0:
            raise ValueError("--invalid-ratio must be between 0 and 1")
        spec.generation_settings.mode = GenerationMode(mode)
        spec.generation_settings.invalid_ratio = invalid_ratio
    elif invalid_ratio:
        raise ValueError("--invalid-ratio requires --mode mixed or --mode negative")
    else:
        spec.generation_settings.mode = GenerationMode(mode)
