"""Persist generation artifacts for CLI workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.io.writers import dataset_spec_to_yaml


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
    output.write_text(dataset_spec_to_yaml(spec))


def write_dataset_generation_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    report: Any,
    output: Path | None,
    business_report: Any | None = None,
    profile_artifact_name: str = "csv_profile.json",
) -> None:
    artifact_dir = output.parent if output is not None else Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / profile_artifact_name).write_text(profile.model_dump_json(indent=2))
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))


def write_dataset_validation_report(report: Any, output_folder: Path) -> None:
    write_json_artifact(report, output_folder / "validation_report.json")


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
