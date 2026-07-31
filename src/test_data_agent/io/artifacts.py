"""Persist generation artifacts for CLI workflows."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from faker.config import DEFAULT_LOCALE

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.io.writers import (
    dataset_spec_to_json,
    dataset_spec_to_yaml,
    write_bounded_text,
)
from test_data_agent.version import __version__


class BusinessValidationManifest(BaseModel):
    rules_sha256: str | None = None
    rule_count: int = Field(default=0, ge=0)
    rule_pass_count: int = Field(default=0, ge=0)
    rule_fail_count: int = Field(default=0, ge=0)
    valid: bool
    errors_truncated: bool = False
    expected_violation_count: int = Field(default=0, ge=0)
    observed_violation_count: int = Field(default=0, ge=0)
    unexpected_violation_count: int = Field(default=0, ge=0)
    missing_expected_violation_count: int = Field(default=0, ge=0)
    expectations_met: bool = True


class ReproducibilityEvidence(BaseModel):
    guarantee: Literal["same_environment_logical"] = "same_environment_logical"
    byte_identical_across_versions: Literal[False] = False
    python_implementation: str
    python_version: str
    dependencies: dict[str, str]
    dependencies_sha256: str
    locale: str
    serializer: str
    generator_algorithm_version: str
    output_sha256: dict[str, str]


class GenerationManifest(BaseModel):
    artifact_type: Literal["synthetic_dataset"] = "synthetic_dataset"
    package_version: str = __version__
    dataset_spec_schema_version: str
    spec_sha256: str
    seed: int
    output_format: OutputFormat
    row_counts: dict[str, int]
    validation_valid: bool
    business_validation: BusinessValidationManifest | None = None
    reproducibility: ReproducibilityEvidence | None = None
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


def write_json_artifact(payload: Any, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump_json"):
        write_bounded_text(payload.model_dump_json(indent=2), output)
        return
    write_bounded_text(json.dumps(payload, indent=2, sort_keys=True, default=str), output)


def write_json_artifact_atomic(payload: Any, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=output.suffix,
    )
    temporary_path = Path(temporary_name)
    os.close(descriptor)
    try:
        write_json_artifact(payload, temporary_path)
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_dataset_profile_artifact(profile: DatasetProfile, output: Path) -> None:
    write_json_artifact(profile, output)


def write_dataset_spec_artifact(spec: DatasetSpec, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".json":
        write_bounded_text(dataset_spec_to_json(spec), output)
    else:
        write_bounded_text(dataset_spec_to_yaml(spec), output)


def write_dataset_spec_artifact_atomic(spec: DatasetSpec, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=output.suffix,
    )
    temporary_path = Path(temporary_name)
    os.close(descriptor)
    try:
        write_dataset_spec_artifact(spec, temporary_path)
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_dataset_generation_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    report: Any,
    output: Path | None,
    business_report: Any | None = None,
    profile_artifact_name: str = "csv_profile.json",
    row_counts: dict[str, int] | None = None,
) -> None:
    artifact_dir = output.parent if output is not None else Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_bounded_text(profile.model_dump_json(indent=2), artifact_dir / profile_artifact_name)
    write_bounded_text(spec.model_dump_json(indent=2), artifact_dir / "dataset_spec.json")
    write_bounded_text(report.model_dump_json(indent=2), artifact_dir / "validation_report.json")
    if business_report is not None:
        write_bounded_text(
            business_report.model_dump_json(indent=2),
            artifact_dir / "business_validation_report.json",
        )
    write_generation_manifest(
        spec,
        seed=spec.generation_settings.seed or 0,
        output_format=spec.generation_settings.output_format,
        row_counts=row_counts or {entity.name: entity.row_count for entity in spec.entities},
        validation_valid=bool(
            report.valid
            and (
                business_report is None
                or spec.generation_settings.mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}
                or bool(business_report.valid)
            )
        ),
        business_report=business_report,
        output_folder=artifact_dir,
    )


def write_dataset_validation_report(report: Any, output_folder: Path) -> None:
    write_json_artifact(report, output_folder / "validation_report.json")


def write_generation_manifest(
    spec: DatasetSpec,
    *,
    seed: int,
    output_format: OutputFormat,
    row_counts: dict[str, int],
    validation_valid: bool,
    output_folder: Path,
    business_report: Any | None = None,
) -> GenerationManifest:
    manifest = GenerationManifest(
        dataset_spec_schema_version=spec.schema_version,
        spec_sha256=dataset_spec_fingerprint(spec),
        seed=seed,
        output_format=output_format,
        row_counts=row_counts,
        validation_valid=validation_valid,
        business_validation=business_validation_manifest(business_report),
        reproducibility=reproducibility_evidence(spec, output_format, output_folder),
    )
    write_json_artifact(manifest, output_folder / "generation_manifest.json")
    return manifest


def reproducibility_evidence(
    spec: DatasetSpec,
    output_format: OutputFormat,
    output_folder: Path,
) -> ReproducibilityEvidence:
    dependencies = {
        name: importlib.metadata.version(name)
        for name in ["Faker", "pydantic", "PyYAML"]
    }
    if output_format == OutputFormat.PARQUET:
        dependencies["pyarrow"] = importlib.metadata.version("pyarrow")
    dependency_payload = json.dumps(
        dependencies,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    serializer = (
        f"pyarrow-{dependencies['pyarrow']}"
        if output_format == OutputFormat.PARQUET
        else f"python-stdlib-{output_format.value}"
    )
    return ReproducibilityEvidence(
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        dependencies=dependencies,
        dependencies_sha256=hashlib.sha256(dependency_payload).hexdigest(),
        locale=spec.generation_settings.locale or DEFAULT_LOCALE,
        serializer=serializer,
        generator_algorithm_version=__version__,
        output_sha256=artifact_hashes(output_folder),
    )


def artifact_hashes(output_folder: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(output_folder.rglob("*")):
        if not path.is_file() or path.name == "generation_manifest.json":
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        hashes[path.relative_to(output_folder).as_posix()] = digest.hexdigest()
    return hashes


def business_validation_manifest(
    report: Any | None,
) -> BusinessValidationManifest | None:
    if report is None:
        return None
    return BusinessValidationManifest(
        rules_sha256=getattr(report, "rules_sha256", None),
        rule_count=int(getattr(report, "rule_count", 0)),
        rule_pass_count=int(getattr(report, "rule_pass_count", 0)),
        rule_fail_count=int(getattr(report, "rule_fail_count", 0)),
        valid=bool(report.valid),
        errors_truncated=any(
            bool(getattr(result, "errors_truncated", False))
            for result in getattr(report, "results", [])
        ),
        expected_violation_count=int(
            getattr(report, "expected_violation_count", 0)
        ),
        observed_violation_count=int(
            getattr(report, "observed_violation_count", 0)
        ),
        unexpected_violation_count=int(
            getattr(report, "unexpected_violation_count", 0)
        ),
        missing_expected_violation_count=int(
            getattr(report, "missing_expected_violation_count", 0)
        ),
        expectations_met=bool(getattr(report, "expectations_met", True)),
    )


def dataset_spec_fingerprint(spec: DatasetSpec) -> str:
    return model_fingerprint(spec)


def dataset_profile_fingerprint(profile: DatasetProfile) -> str:
    return model_fingerprint(profile)


def model_fingerprint(model: BaseModel) -> str:
    canonical = json.dumps(
        model.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_dataset_review_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    report: Any,
    output_folder: Path,
) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    write_dataset_profile_artifact(profile, output_folder / "profile.json")
    write_dataset_spec_artifact(spec, output_folder / "dataset_spec.yaml")
    write_dataset_validation_report(report, output_folder)
