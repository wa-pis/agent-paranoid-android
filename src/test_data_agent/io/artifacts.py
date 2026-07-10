"""Persist generation artifacts for CLI workflows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.writers import dataset_spec_to_json, dataset_spec_to_yaml
from test_data_agent.version import __version__


class GenerationManifest(BaseModel):
    artifact_type: Literal["synthetic_dataset"] = "synthetic_dataset"
    package_version: str = __version__
    dataset_spec_schema_version: str
    spec_sha256: str
    seed: int
    output_format: OutputFormat
    row_counts: dict[str, int]
    validation_valid: bool
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


def write_json_artifact(payload: Any, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump_json"):
        output.write_text(payload.model_dump_json(indent=2))
        return
    output.write_text(str(payload))


def write_dataset_profile_artifact(profile: DatasetProfile, output: Path) -> None:
    write_json_artifact(profile, output)


def write_dataset_spec_artifact(spec: DatasetSpec, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".json":
        output.write_text(dataset_spec_to_json(spec))
    else:
        output.write_text(dataset_spec_to_yaml(spec))


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
    (artifact_dir / profile_artifact_name).write_text(profile.model_dump_json(indent=2))
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    write_generation_manifest(
        spec,
        seed=spec.generation_settings.seed or 0,
        output_format=spec.generation_settings.output_format,
        row_counts=row_counts or {entity.name: entity.row_count for entity in spec.entities},
        validation_valid=bool(report.valid),
        output_folder=artifact_dir,
    )
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))


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
) -> GenerationManifest:
    manifest = GenerationManifest(
        dataset_spec_schema_version=spec.schema_version,
        spec_sha256=dataset_spec_fingerprint(spec),
        seed=seed,
        output_format=output_format,
        row_counts=row_counts,
        validation_valid=validation_valid,
    )
    write_json_artifact(manifest, output_folder / "generation_manifest.json")
    return manifest


def dataset_spec_fingerprint(spec: DatasetSpec) -> str:
    canonical = json.dumps(
        spec.model_dump(mode="json"),
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
