"""Persist generation artifacts for CLI workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.spec import GenerationSpec


def write_generation_artifacts(
    spec: GenerationSpec,
    report: Any,
    output: Path | None,
    business_report: Any | None = None,
) -> None:
    artifact_dir = output.parent if output is not None else Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))


def write_dataset_generation_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    report: Any,
    output: Path,
    business_report: Any | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    (output.parent / "csv_profile.json").write_text(profile.model_dump_json(indent=2))
    artifact_dir = output.parent
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))
