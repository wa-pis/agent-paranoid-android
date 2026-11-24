"""Validated, bounded-tile CSV generation inside an existing bundle transaction."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from test_data_agent.adapters.parallel_generation import (
    ParallelGenerationError,
    ParallelGenerationPolicy,
    _visit_generated_tiles,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.fingerprints import model_fingerprint
from test_data_agent.core.limits import (
    GenerationBudget,
    GenerationLimitError,
    enforce_output_payload_size,
    enforce_row_count_limit,
)
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.constraint_solver import solve_constraints
from test_data_agent.generation.limits import estimate_dataset_output_bytes
from test_data_agent.generation.tiled_generator import TILE_ROWS
from test_data_agent.io.path_policy import atomic_binary_writer
from test_data_agent.io.csv_encoding import encode_csv_cell
from test_data_agent.io.writers import safe_entity_artifact_path
from test_data_agent.safety import assert_spec_safe
from test_data_agent.validation.reconciliation import (
    DatasetValidationReport,
    GenerationValidationError,
    _validate_generated_dataset,
)


class StreamingCsvError(ValueError):
    """A value-free failure of optional streaming CSV generation or output."""


def can_stream_csv(spec: DatasetSpec) -> bool:
    # shortcut: global rules retain full-dataset solving until a streaming solver exists.
    return bool(
        len(spec.entities) == 1 and spec.entities[0].fields
        and spec.generation_settings.mode == GenerationMode.VALID
        and not spec.relationships and not spec.constraints
        and spec.business_rules is None and not spec.relational_scenarios
        and spec.generation_settings.execution_policy is None
    )


def write_streaming_csv(
    spec: DatasetSpec,
    *,
    output_folder: Path,
    seed: int,
    policy: ParallelGenerationPolicy,
    budget: GenerationBudget,
) -> DatasetValidationReport:
    """Validate every tile and global keys before atomically publishing one CSV."""
    failed = False
    report: DatasetValidationReport | None = None
    try:
        snapshot = DatasetSpec.model_validate(spec.model_dump(warnings=False))
        if not can_stream_csv(snapshot):
            raise StreamingCsvError("specification does not support streaming CSV")
        if type(seed) is not int or seed < 0:
            raise StreamingCsvError("streaming CSV requires a nonnegative integer seed")
        assert_spec_safe(snapshot)
        entity = snapshot.entities[0]
        enforce_row_count_limit(entity.row_count, max_count=policy.max_rows)
        if entity.row_count * len(entity.fields) > policy.max_cells:
            raise GenerationLimitError("streaming CSV exceeds its cell budget")
        in_flight_spec = snapshot.model_copy(deep=True)
        in_flight_spec.entities[0].row_count = min(entity.row_count, TILE_ROWS * policy.workers)
        enforce_output_payload_size(
            estimate_dataset_output_bytes(in_flight_spec), label="estimated streaming CSV in-flight data",
        )
        budget.check("streaming CSV setup")
        output = safe_entity_artifact_path(output_folder, entity.name, ".csv")
        fields = [field.name for field in entity.fields]
        seen: set[Any] = set()
        count = total_bytes = 0
        with atomic_binary_writer(
            output, check_publication=lambda: budget.check("streaming CSV publication"),
        ) as handle:
            def consume(entity_index: int, start: int, rows: list[dict[str, Any]]) -> None:
                nonlocal count, total_bytes, report
                budget.check("streaming CSV validation")
                if (entity_index != 0 or start != count or not 0 < len(rows) <= TILE_ROWS
                        or count + len(rows) > entity.row_count):
                    raise GenerationValidationError("streaming CSV row sequence is invalid")
                batch_spec = snapshot.model_copy(deep=True)
                batch_spec.entities[0].row_count = len(rows)
                data = {entity.name: rows}
                solve_constraints(data, batch_spec, seed=seed, budget=budget)
                current_report, normalized = _validate_generated_dataset(data, batch_spec, budget=budget)
                if not current_report.valid:
                    raise GenerationValidationError("streaming CSV failed dataset validation")
                if entity.primary_key is not None:
                    for row in normalized[entity.name]:
                        key = row[entity.primary_key]
                        if key in (None, "") or key in seen:
                            raise GenerationValidationError("streaming CSV primary keys are not unique")
                        seen.add(key)
                budget.check("streaming CSV encoding")
                text = StringIO(newline="")
                writer = csv.writer(text)
                if count == 0:
                    writer.writerow([encode_csv_cell(name) for name in fields])
                writer.writerows([
                    encode_csv_cell(row[name]) for name in fields
                ] for row in rows)
                payload = text.getvalue().encode("utf-8")
                enforce_output_payload_size(total_bytes + len(payload), label="streaming CSV")
                budget.check("streaming CSV write")
                handle.write(payload)
                total_bytes += len(payload)
                count += len(rows)
                report = current_report

            _visit_generated_tiles(snapshot, seed, policy=policy, budget=budget, consume=consume)
            if count != entity.row_count or report is None:
                raise GenerationValidationError("streaming CSV row count is invalid")
            if entity.primary_key is not None and len(seen) != count:
                raise GenerationValidationError("streaming CSV primary key count is invalid")
            if report.utility is not None:
                report.utility.spec_sha256 = model_fingerprint(snapshot)
            budget.check("streaming CSV final validation")
    except (StreamingCsvError, GenerationLimitError, GenerationValidationError,
            ParallelGenerationError):
        raise
    except Exception:
        failed = True
    if failed:
        raise StreamingCsvError("streaming CSV generation or output failed")
    assert report is not None
    return report
