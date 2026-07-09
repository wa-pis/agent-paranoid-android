"""I/O helpers for deprecated GenerationSpec compatibility workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from test_data_agent.adapters import (
    LegacyGenerationResult,
    generate_legacy_compatibility_result,
    validate_legacy_rows_file,
)
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_generation_artifacts, write_json_artifact
from test_data_agent.io.workflows import warn_deprecated_generation_spec_compatibility
from test_data_agent.io.writers import write_tabular_rows


BusinessRulesApplier = Callable[[dict[str, list[dict[str, Any]]], int], Any | None]


def generate_legacy_spec_artifacts(
    spec_path: Path,
    *,
    row_count: int | None = None,
    seed: int | None = None,
    output_format: OutputFormat | None = None,
    output_path: Path | None = None,
    mode: str = "valid",
    invalid_ratio: float = 0.0,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> tuple[LegacyGenerationResult, Any | None]:
    warn_deprecated_generation_spec_compatibility("generate")
    result = generate_legacy_compatibility_result(
        spec_path,
        row_count=row_count,
        seed=seed,
        output_format=output_format,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    business_report = None
    if business_rules_applier is not None:
        business_report = business_rules_applier(
            {result.spec.table.name: result.rows},
            result.spec.seed or 0,
        )
    write_tabular_rows(result.rows, result.spec, output_path)
    write_generation_artifacts(
        result.spec,
        result.report,
        output_path,
        business_report=business_report,
    )
    return result, business_report


def validate_legacy_spec_artifacts(
    spec_path: Path,
    rows_path: Path,
    *,
    output_path: Path | None = None,
) -> Any:
    warn_deprecated_generation_spec_compatibility("validate")
    report = validate_legacy_rows_file(spec_path, rows_path)
    if output_path is not None:
        write_json_artifact(report, output_path)
    else:
        print(report.model_dump_json(indent=2))
    return report
