"""Command helpers for DatasetSpec-oriented CLI flows."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_json_artifact
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import generate_dataset_artifacts
from test_data_agent.validation import DatasetValidationReport, validate_dataset


def is_dataset_spec_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return True
    if suffix != ".json":
        return False
    try:
        return isinstance(load_profile_or_spec(path), DatasetSpec)
    except Exception:
        return False


def generate_dataset_from_spec_path(
    spec_path: Path,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
) -> int:
    spec = load_dataset_spec(spec_path)
    return generate_dataset_artifacts(
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
    )


def validate_dataset_artifacts(
    spec_path: Path,
    rows_path: Path,
    *,
    output_path: Path | None = None,
) -> DatasetValidationReport:
    spec = load_dataset_spec(spec_path)
    rows_by_entity = load_dataset_rows(rows_path)
    report = validate_dataset(rows_by_entity, spec)
    if output_path is not None:
        write_json_artifact(report, output_path)
    return report
