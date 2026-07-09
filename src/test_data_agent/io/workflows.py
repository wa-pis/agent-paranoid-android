"""Workflow helpers for DatasetSpec-oriented CLI commands."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.artifacts import write_dataset_validation_report
from test_data_agent.io.writers import write_dataset_rows
from test_data_agent.validation import validate_dataset


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
