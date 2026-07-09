"""Workflow helpers for DatasetSpec-oriented CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io.artifacts import (
    write_dataset_generation_artifacts,
    write_dataset_review_artifacts,
    write_dataset_validation_report,
)
from test_data_agent.io.writers import write_dataset_rows, write_single_entity_rows
from test_data_agent.validation import DatasetValidationReport, validate_dataset


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
