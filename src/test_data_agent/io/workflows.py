"""Workflow helpers for DatasetSpec-oriented CLI commands."""

from __future__ import annotations

import inspect
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel

from test_data_agent.adapters import (
    csv_file_to_dataset_profile,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import (
    GenerationBudget,
    enforce_output_capacity,
    enforce_output_folder_size,
    enforce_output_payload_size,
    enforce_row_count_limit,
    max_generation_count as configured_max_generation_count,
)
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
    write_json_artifact,
)
from test_data_agent.io.writers import write_dataset_rows, write_single_entity_rows
from test_data_agent.safety import (
    assert_no_csv_folder_source_rows,
    assert_no_csv_source_rows,
    assert_profile_safe,
)
from test_data_agent.validation import DatasetValidationReport, validate_dataset


BusinessRulesApplier = Callable[..., Any | None]


class DatasetGenerationResult(BaseModel):
    seed: int
    output_format: OutputFormat
    mode: GenerationMode
    row_counts: dict[str, int]
    validation: DatasetValidationReport
    business_validation: Any | None = None
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


def generate_dataset_bundle(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> DatasetGenerationResult:
    effective_spec = spec.model_copy(deep=True)
    if not effective_spec.entities:
        raise ValueError("dataset spec must contain at least one entity")
    effective_output_format = output_format or effective_spec.generation_settings.output_format
    max_count = max_generation_count()
    if count is not None:
        if count < 1:
            raise ValueError("count must be positive")
        if count > max_count:
            raise ValueError(f"count must be <= {max_count}")
        for entity in effective_spec.entities:
            entity.row_count = count
    enforce_generation_row_count_limits(effective_spec, max_count=max_count)
    effective_seed = effective_spec.generation_settings.seed if seed is None else seed
    if effective_seed is None:
        effective_seed = 0
    if effective_seed < 0:
        raise ValueError("seed must be non-negative")
    effective_spec.generation_settings.seed = effective_seed
    effective_spec.generation_settings.output_format = effective_output_format

    budget = prepare_generation_budget(effective_spec, output_folder)
    rows_by_entity = generate_dataset(effective_spec, seed=effective_seed, budget=budget)
    budget.check("dataset generation")
    business_report = (
        invoke_business_rules_applier(
            business_rules_applier,
            rows_by_entity,
            effective_seed,
            effective_spec,
        )
        if business_rules_applier is not None
        else None
    )
    budget.check("business rule application")
    temp_folder = make_temp_output_folder(output_folder)
    try:
        write_dataset_rows(rows_by_entity, effective_output_format, temp_folder)
        budget.check("dataset export")
        report = validate_dataset(rows_by_entity, effective_spec)
        budget.check("dataset validation")
        generation_valid = report.valid and business_report_is_valid(
            business_report,
            effective_spec.generation_settings.mode,
        )
        write_dataset_spec_artifact(effective_spec, temp_folder / "dataset_spec.yaml")
        write_dataset_validation_report(report, temp_folder)
        if business_report is not None:
            write_json_artifact(business_report, temp_folder / "business_validation_report.json")
        row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
        write_generation_manifest(
            effective_spec,
            seed=effective_seed,
            output_format=effective_output_format,
            row_counts=row_counts,
            validation_valid=generation_valid,
            output_folder=temp_folder,
        )
        enforce_output_folder_size(temp_folder)
        budget.check("artifact publication")
        commit_temp_output_folder(temp_folder, output_folder)
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise
    row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
    return DatasetGenerationResult(
        seed=effective_seed,
        output_format=effective_output_format,
        mode=effective_spec.generation_settings.mode,
        row_counts=row_counts,
        validation=report,
        business_validation=business_report,
    )


def generate_dataset_artifacts(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    result = generate_dataset_bundle(
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
        business_rules_applier=business_rules_applier,
    )
    return 0 if result_is_valid(result) else 1


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
    enforce_generation_row_count_limits(spec)
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
    ensure_paths_distinct(input_path, output_path)
    require_output_suffix(output_path, {".json"}, "profile output")
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
    budget: GenerationBudget | None = None,
) -> DatasetValidationReport:
    budget = budget or prepare_generation_budget(spec, output_path or Path.cwd())
    rows_by_entity = rows_by_entity or generate_dataset(
        spec,
        seed=spec.generation_settings.seed or 0,
        budget=budget,
    )
    budget.check("dataset generation")
    report = validate_dataset(rows_by_entity, spec)
    budget.check("dataset validation")
    if output_path is None:
        write_single_entity_rows(rows_by_entity, spec.generation_settings.output_format, output_path)
        write_dataset_generation_artifacts(
            profile,
            spec,
            report,
            output_path,
            business_report=business_report,
            profile_artifact_name=profile_artifact_name,
            row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
        )
        budget.check("artifact publication")
        return report

    temp_folder = make_temp_output_folder(output_path.parent / output_path.stem)
    temp_output_path = temp_folder / output_path.name
    try:
        write_single_entity_rows(rows_by_entity, spec.generation_settings.output_format, temp_output_path)
        write_dataset_generation_artifacts(
            profile,
            spec,
            report,
            temp_output_path,
            business_report=business_report,
            profile_artifact_name=profile_artifact_name,
            row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
        )
        enforce_output_folder_size(temp_folder)
        budget.check("artifact publication")
        commit_single_entity_bundle(temp_folder, output_path.parent)
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise
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
    budget = prepare_generation_budget(spec, output_path)
    rows_by_entity = generate_dataset(
        spec,
        seed=spec.generation_settings.seed or 0,
        budget=budget,
    )
    budget.check("dataset generation")
    business_report = None
    if business_rules_applier is not None:
        business_report = invoke_business_rules_applier(
            business_rules_applier,
            rows_by_entity,
            spec.generation_settings.seed or 0,
            spec,
        )
        budget.check("business rule application")
    report = generate_single_entity_profile_artifacts(
        profile,
        spec,
        output_path=output_path,
        rows_by_entity=rows_by_entity,
        business_report=business_report,
        profile_artifact_name=profile_artifact_name,
        budget=budget,
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
    ensure_paths_distinct(input_path, output_path)
    profile = csv_file_to_dataset_profile(input_path, table_name=table_name)
    spec = build_dataset_spec_from_profile(
        profile,
        count=count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    budget = prepare_generation_budget(spec, output_path)
    rows_by_entity = generate_dataset(spec, seed=seed, budget=budget)
    budget.check("dataset generation")
    business_report = None
    if business_rules_applier is not None:
        business_report = invoke_business_rules_applier(
            business_rules_applier,
            rows_by_entity,
            seed,
            spec,
        )
        budget.check("business rule application")
    assert_no_csv_source_rows(input_path, rows_by_entity[spec.entities[0].name])
    report = generate_single_entity_profile_artifacts(
        profile,
        spec,
        output_path=output_path,
        rows_by_entity=rows_by_entity,
        business_report=business_report,
        profile_artifact_name="csv_profile.json",
        budget=budget,
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
    if source_folder is not None:
        ensure_folders_distinct(source_folder, output_folder)
    ensure_empty_output_folder(output_folder)
    effective_spec = spec.model_copy(deep=True)
    effective_spec.generation_settings.seed = seed
    effective_spec.generation_settings.output_format = output_format
    enforce_generation_row_count_limits(effective_spec)
    budget = prepare_generation_budget(effective_spec, output_folder)
    rows_by_entity = generate_dataset(effective_spec, seed=seed, budget=budget)
    budget.check("dataset generation")
    temp_folder = make_temp_output_folder(output_folder)
    try:
        if source_folder is not None:
            assert_no_csv_folder_source_rows(source_folder, rows_by_entity)
        write_dataset_rows(rows_by_entity, output_format, temp_folder)
        budget.check("dataset export")
        report = validate_dataset(rows_by_entity, effective_spec)
        budget.check("dataset validation")
        write_dataset_review_bundle(profile, effective_spec, report, temp_folder)
        write_generation_manifest(
            effective_spec,
            seed=seed,
            output_format=output_format,
            row_counts={name: len(rows) for name, rows in rows_by_entity.items()},
            validation_valid=report.valid,
            output_folder=temp_folder,
        )
        enforce_output_folder_size(temp_folder)
        budget.check("artifact publication")
        commit_temp_output_folder(temp_folder, output_folder)
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise
    return 0 if report.valid else 1


def business_report_is_valid(report: Any | None, mode: GenerationMode) -> bool:
    if report is None or mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        return True
    return bool(report.valid)


def invoke_business_rules_applier(
    applier: BusinessRulesApplier,
    rows_by_entity: dict[str, list[dict[str, Any]]],
    seed: int,
    spec: DatasetSpec,
) -> Any | None:
    parameters = list(inspect.signature(applier).parameters.values())
    if any(parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in parameters):
        return applier(rows_by_entity, seed, spec)
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
    ]
    if len(positional) >= 3:
        return applier(rows_by_entity, seed, spec)
    return applier(rows_by_entity, seed)


def result_is_valid(result: DatasetGenerationResult) -> bool:
    return result.validation.valid and business_report_is_valid(
        result.business_validation,
        result.mode,
    )


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


def max_generation_count() -> int:
    return configured_max_generation_count()


def enforce_generation_row_count_limits(spec: DatasetSpec, *, max_count: int | None = None) -> None:
    for entity in spec.entities:
        try:
            enforce_row_count_limit(entity.row_count, max_count=max_count)
        except ValueError as exc:
            effective_max = max_generation_count() if max_count is None else max_count
            raise ValueError(f"entity row_count must be <= {effective_max}: {entity.name}") from exc


def prepare_generation_budget(spec: DatasetSpec, output_path: Path) -> GenerationBudget:
    target_folder = output_path if not output_path.suffix else output_path.parent
    enforce_output_capacity(target_folder)
    enforce_output_payload_size(
        estimate_dataset_output_bytes(spec),
        label="estimated generated data",
    )
    return GenerationBudget()


def estimate_dataset_output_bytes(spec: DatasetSpec) -> int:
    total = len(spec.model_dump_json().encode("utf-8")) * 2 + 65_536
    for entity in spec.entities:
        row_bytes = 2
        for field in entity.fields:
            row_bytes += len(field.name.encode("utf-8")) + estimate_field_output_bytes(field) + 8
        total += entity.row_count * row_bytes * 2
    return total


def estimate_field_output_bytes(field: Any) -> int:
    if field.is_identifier:
        return len(field.name.encode("utf-8")) + 64
    if field.sensitive:
        return 128
    if field.data_type != "string":
        return 64
    distribution = field.distribution or {}
    if distribution.get("kind") == "categorical":
        categories = distribution.get("categories") or []
        return max(
            (
                len(json.dumps(category.get("value"), default=str).encode("utf-8"))
                for category in categories
            ),
            default=16,
        )
    maximum = int(distribution.get("max_length", 12))
    return max(1, maximum) + 4


def make_temp_output_folder(output_folder: Path) -> Path:
    output_folder.parent.mkdir(parents=True, exist_ok=True)
    enforce_output_capacity(output_folder.parent)
    return Path(tempfile.mkdtemp(prefix=f".{output_folder.name}.", dir=output_folder.parent))


def commit_temp_output_folder(temp_folder: Path, output_folder: Path) -> None:
    if output_folder.exists():
        if not output_folder.is_dir():
            raise ValueError("generation output must be a folder")
        if any(output_folder.iterdir()):
            raise ValueError("generation output folder must be empty")
        output_folder.rmdir()
    temp_folder.replace(output_folder)


def commit_single_entity_bundle(temp_folder: Path, output_folder: Path) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    for path in sorted(temp_folder.iterdir()):
        path.replace(output_folder / path.name)
    temp_folder.rmdir()


def ensure_paths_distinct(first: Path, second: Path) -> None:
    if first.resolve(strict=False) == second.resolve(strict=False):
        raise ValueError("input and output paths must be different")


def ensure_folders_distinct(source_folder: Path, output_folder: Path) -> None:
    if source_folder.resolve(strict=True) == output_folder.resolve(strict=False):
        raise ValueError("source and output folders must be different")


def ensure_empty_output_folder(output_folder: Path) -> None:
    if output_folder.exists() and not output_folder.is_dir():
        raise ValueError("generation output must be a folder")
    if output_folder.exists() and any(output_folder.iterdir()):
        raise ValueError("generation output folder must be empty")


def require_output_suffix(path: Path, allowed: set[str], label: str) -> None:
    if path.suffix.lower() not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{label} must use one of: {expected}")
