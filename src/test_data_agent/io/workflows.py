"""Workflow helpers for DatasetSpec-oriented CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel

from test_data_agent.adapters import (
    csv_file_to_dataset_profile,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io.artifacts import (
    write_dataset_generation_artifacts,
    write_dataset_profile_artifact,
    write_dataset_review_artifacts as write_dataset_review_bundle,
    write_dataset_spec_artifact,
    write_dataset_validation_report,
    write_generation_manifest,
)
from test_data_agent.io.writers import write_dataset_rows, write_single_entity_rows
from test_data_agent.safety import (
    assert_no_csv_folder_source_rows,
    assert_no_csv_source_rows,
    assert_profile_safe,
)
from test_data_agent.validation import DatasetValidationReport, validate_dataset


BusinessRulesApplier = Callable[[dict[str, list[dict[str, Any]]], int], Any | None]


class DatasetGenerationResult(BaseModel):
    seed: int
    output_format: OutputFormat
    row_counts: dict[str, int]
    validation: DatasetValidationReport
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


def generate_dataset_bundle(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
) -> DatasetGenerationResult:
    effective_spec = spec.model_copy(deep=True)
    if not effective_spec.entities:
        raise ValueError("dataset spec must contain at least one entity")
    effective_output_format = output_format or effective_spec.generation_settings.output_format
    if count is not None:
        if count < 1:
            raise ValueError("count must be positive")
        for entity in effective_spec.entities:
            entity.row_count = count
    effective_seed = effective_spec.generation_settings.seed if seed is None else seed
    if effective_seed is None:
        effective_seed = 0
    if effective_seed < 0:
        raise ValueError("seed must be non-negative")
    effective_spec.generation_settings.seed = effective_seed
    effective_spec.generation_settings.output_format = effective_output_format

    rows_by_entity = generate_dataset(effective_spec, seed=effective_seed)
    write_dataset_rows(rows_by_entity, effective_output_format, output_folder)
    report = validate_dataset(rows_by_entity, effective_spec)
    write_dataset_spec_artifact(effective_spec, output_folder / "dataset_spec.yaml")
    write_dataset_validation_report(report, output_folder)
    row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
    write_generation_manifest(
        effective_spec,
        seed=effective_seed,
        output_format=effective_output_format,
        row_counts=row_counts,
        validation_valid=report.valid,
        output_folder=output_folder,
    )
    return DatasetGenerationResult(
        seed=effective_seed,
        output_format=effective_output_format,
        row_counts=row_counts,
        validation=report,
    )


def generate_dataset_artifacts(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
) -> int:
    result = generate_dataset_bundle(
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
    )
    return 0 if result.validation.valid else 1


def build_dataset_spec_from_profile(
    profile: DatasetProfile,
    *,
    count: int,
    seed: int,
    output_format: OutputFormat | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
) -> DatasetSpec:
    assert_profile_safe(profile)
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
    assert_profile_safe(profile)
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
    assert_profile_safe(profile)
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
        row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
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
    assert_no_csv_source_rows(input_path, rows_by_entity[spec.entities[0].name])
    report = validate_dataset(rows_by_entity, spec)
    write_single_entity_rows(rows_by_entity, output_format, output_path)
    write_dataset_generation_artifacts(
        profile,
        spec,
        report,
        output_path,
        business_report=business_report,
        row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
    )
    return report, business_report


def generate_dataset_review_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat,
    seed: int,
    source_folder: Path | None = None,
) -> int:
    assert_profile_safe(profile)
    effective_spec = spec.model_copy(deep=True)
    effective_spec.generation_settings.seed = seed
    effective_spec.generation_settings.output_format = output_format
    rows_by_entity = generate_dataset(effective_spec, seed=seed)
    if source_folder is not None:
        assert_no_csv_folder_source_rows(source_folder, rows_by_entity)
    write_dataset_rows(rows_by_entity, output_format, output_folder)
    report = validate_dataset(rows_by_entity, effective_spec)

    write_dataset_review_bundle(profile, effective_spec, report, output_folder)
    write_generation_manifest(
        effective_spec,
        seed=seed,
        output_format=output_format,
        row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
        validation_valid=report.valid,
        output_folder=output_folder,
    )
    return 0 if report.valid else 1


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
