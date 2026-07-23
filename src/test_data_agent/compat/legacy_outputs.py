"""Compatibility output helpers for deprecated GenerationSpec workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from test_data_agent.core.limits import enforce_output_payload_size
from test_data_agent.io.writers import rows_to_csv, write_bounded_text, write_parquet
from test_data_agent.spec import GenerationSpec


def write_tabular_rows(rows: list[dict[str, Any]], spec: GenerationSpec, output: Path | None) -> None:
    if spec.output_format == "parquet":
        if output is None:
            raise SystemExit("Parquet output requires --output")
        write_parquet(rows, output)
        return

    if spec.output_format == "csv":
        text = rows_to_csv(rows)
    else:
        text = json.dumps(rows, indent=2, sort_keys=True)

    if output is None:
        enforce_output_payload_size(len(text.encode("utf-8")), label="standard output")
        print(text)
    else:
        write_bounded_text(text, output)


def write_generation_artifacts(
    spec: GenerationSpec,
    report: Any,
    output: Path | None,
    business_report: Any | None = None,
) -> None:
    artifact_dir = output.parent if output is not None else Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_bounded_text(spec.model_dump_json(indent=2), artifact_dir / "generation_spec.json")
    write_bounded_text(report.model_dump_json(indent=2), artifact_dir / "validation_report.json")
    if business_report is not None:
        write_bounded_text(
            business_report.model_dump_json(indent=2),
            artifact_dir / "business_validation_report.json",
        )


__all__ = [
    "write_generation_artifacts",
    "write_tabular_rows",
]
