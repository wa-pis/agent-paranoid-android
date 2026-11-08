"""Bounded streaming publication for explicitly opted-in independent datasets."""
from __future__ import annotations

import csv
import io
import json
import multiprocessing
import os
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, TYPE_CHECKING

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.execution_policy import MAX_SCALABLE_JSON_ROW_CHARS
from test_data_agent.core.generation_progress import GenerationProgress
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError, enforce_output_capacity, enforce_output_folder_size, max_output_bytes
from test_data_agent.core.settings import OutputFormat, MAX_GENERATION_SEED
from test_data_agent.generation.scalable import RowTask, RowBatch, check_scalable_spec, generate_task, resident_high_water_bytes
from test_data_agent.io.artifacts import write_dataset_spec_artifact, write_dataset_profile_artifact, write_dataset_validation_report, write_generation_manifest, write_json_artifact
from test_data_agent.io.csv_encoding import encode_csv_cell
from test_data_agent.io.path_policy import make_staging_directory, discard_staging_directory, publish_directory
from test_data_agent.io.writers import safe_entity_artifact_path, typed_parquet_table, json_decimal
from test_data_agent.validation.reconciliation import DatasetValidationReport, ValidationSection, ValidationUtilityEvidence
from test_data_agent.core.fingerprints import model_fingerprint


from test_data_agent.trino_work_budget import generation_budget_for_invocation, current_query_work_budget

if TYPE_CHECKING:
    from test_data_agent.io.workflows import DatasetGenerationResult


class _LimitedWriter(io.BufferedWriter):
    def __init__(self, path: Path, limit: int) -> None:
        super().__init__(path.open("xb", buffering=0))
        self.limit = limit

    def write(self, data: Any) -> int:
        if self.tell()+len(data) > self.limit:
            raise GenerationLimitError("streaming output exceeds output or temporary-disk policy")
        return super().write(data)


BatchCheck = Callable[[dict[str, list[dict[str, Any]]]], None]
BeforePublish = Callable[[Path, DatasetValidationReport], None]


def _batches(spec: DatasetSpec, index: int, seed: int, budget: GenerationBudget) -> Generator[RowBatch, None, None]:
    policy = spec.generation_settings.execution_policy
    assert policy is not None
    tasks = (RowTask(spec, index, start, min(policy.batch_size, spec.entities[index].row_count-start), seed)
             for start in range(0, spec.entities[index].row_count, policy.batch_size))
    if policy.workers == 1:
        for task in tasks:
            budget.check("streaming generation")
            yield generate_task(task, budget=budget)
        return
    pool = multiprocessing.get_context("spawn").Pool(policy.workers)
    try:
        while True:
            group = []
            for _ in range(policy.workers):
                next_task = next(tasks, None)
                if next_task is None:
                    break
                group.append(pool.apply_async(generate_task, (next_task,)))
            if not group:
                break
            for pending in group:
                budget.check("parallel generation")
                try:
                    # The parent owns the end-to-end deadline, including blocked workers.
                    request_budget = current_query_work_budget()
                    remaining = budget.remaining_seconds()
                    if request_budget is not None:
                        remaining = min(remaining, request_budget.remaining_invocation_seconds())
                    yield pending.get(timeout=max(.001, remaining))
                except GenerationLimitError:
                    raise GenerationLimitError("scalable worker exceeded its resource policy; reduce workers or batch size, or review the finite budget") from None
                except Exception:
                    raise GenerationLimitError("scalable worker failed or exceeded its deadline; inspect policy and retry") from None
    finally:
        pool.terminate()
        pool.join()


def generate_scalable_bundle(
    spec: DatasetSpec, *, output_folder: Path, seed: int,
    profile: DatasetProfile | None = None, overwrite: bool = False,
    check_batch: BatchCheck | None = None, before_publish: BeforePublish | None = None,
    progress: Callable[[GenerationProgress], None] | None = None,
) -> DatasetGenerationResult:
    from test_data_agent.io.workflows import DatasetGenerationResult
    if type(seed) is not int or not 0 <= seed <= MAX_GENERATION_SEED:
        raise GenerationLimitError('scalable bundle seed must be a nonnegative signed 64-bit integer')
    if spec.generation_settings.seed not in (None, seed):
        raise ValueError('scalable bundle seed must match the reviewed specification')
    if spec.generation_settings.seed is None:
        spec = spec.model_copy(deep=True)
        spec.generation_settings.seed = seed
    check_scalable_spec(spec)
    policy = spec.generation_settings.execution_policy
    assert policy is not None
    if spec.generation_settings.output_format not in {OutputFormat.CSV, OutputFormat.JSON, OutputFormat.PARQUET}:
        raise ValueError("scalable-v1 supports csv, json and parquet")
    budget = generation_budget_for_invocation(max_seconds=policy.max_seconds)
    started = time.monotonic()
    enforce_output_capacity(output_folder.parent)
    stage = make_staging_directory(output_folder)
    counts: dict[str, int] = {}
    peak_workers = 0
    actual_bytes = 0
    generation_seconds = 0.
    writing_seconds = 0.
    task_generation_seconds = 0.
    task_validation_seconds = 0.
    task_count = 0
    completed_rows = 0
    last_update = started
    total_rows = sum(e.row_count for e in spec.entities)
    fingerprint = model_fingerprint(spec)
    try:
        for index, entity in enumerate(spec.entities):
            path = safe_entity_artifact_path(stage, entity.name, '.'+spec.generation_settings.output_format.value)
            parquet = None
            count = 0
            with _LimitedWriter(path, min(policy.max_output_bytes, policy.max_temporary_bytes, max_output_bytes())-actual_bytes) as binary:
                if spec.generation_settings.output_format == OutputFormat.CSV:
                    handle = io.TextIOWrapper(binary, encoding='utf-8', newline='', write_through=True)
                    writer = csv.writer(handle)
                    writer.writerow([encode_csv_cell(f.name) for f in entity.fields])
                else:
                    handle = None
                    writer = None
                if spec.generation_settings.output_format == OutputFormat.JSON:
                    binary.write(b'[')
                try:
                    batches = _batches(spec, index, seed, budget)
                    while True:
                        start = time.monotonic()
                        batch = next(batches, None)
                        generation_seconds += time.monotonic()-start
                        if batch is None:
                            break
                        rows, memory = batch.rows, batch.memory_bytes
                        task_generation_seconds += batch.generation_seconds
                        task_validation_seconds += batch.validation_seconds
                        task_count += 1
                        peak_workers = max(peak_workers, memory*policy.workers)
                        if resident_high_water_bytes()+peak_workers > policy.max_memory_bytes:
                            raise GenerationLimitError("process-tree memory exceeds execution policy")
                        if check_batch is not None:
                            check_batch({entity.name: rows})
                        start = time.monotonic()
                        if writer is not None:
                            writer.writerows([[encode_csv_cell(row[f.name]) for f in entity.fields] for row in rows])
                            assert handle is not None
                            handle.flush()
                        elif spec.generation_settings.output_format == OutputFormat.JSON:
                            for row in rows:
                                if count:
                                    binary.write(b',')
                                payload = json.dumps(row, indent=2, sort_keys=True, default=json_decimal)
                                rendered = payload.replace('\n', '\n  ')
                                if len(rendered) > MAX_SCALABLE_JSON_ROW_CHARS:
                                    raise GenerationLimitError('streamed JSON row exceeds bounded decode size')
                                binary.write(('\n  '+rendered).encode('utf-8'))
                                count += 1
                        else:
                            import pyarrow as pa
                            import pyarrow.parquet as pq
                            table = typed_parquet_table(rows, entity.fields, pa)
                            if parquet is None:
                                parquet = pq.ParquetWriter(binary, table.schema, compression='snappy')
                            parquet.write_table(table)
                        if spec.generation_settings.output_format != OutputFormat.JSON:
                            count += len(rows)
                        writing_seconds += time.monotonic()-start
                        binary.flush()
                        if actual_bytes+os.fstat(binary.fileno()).st_size > min(policy.max_output_bytes, policy.max_temporary_bytes):
                            raise GenerationLimitError("streaming output exceeds output or temporary-disk policy")
                        enforce_output_capacity(stage)
                        budget.check("streaming export")
                        completed_rows += len(rows)
                        now = time.monotonic()
                        if progress is not None and (now-last_update >= 1 or completed_rows == total_rows):
                            remaining = (now-started)*(total_rows-completed_rows)/max(1, completed_rows)
                            progress(GenerationProgress(spec_sha256=fingerprint, phase='generating',
                                rows_completed=completed_rows, rows_total=total_rows, elapsed_seconds=now-started,
                                remaining_seconds_low=remaining*.65, remaining_seconds_high=remaining*1.5))
                            last_update = now
                    if spec.generation_settings.output_format == OutputFormat.JSON:
                        binary.write(b'\n]' if count else b']')
                finally:
                    # Closing the iterator reaps processes even if writing or checks fail.
                    if 'batches' in locals():
                        batches.close()
                    if parquet is not None:
                        parquet.close()
                    if handle is not None:
                        handle.flush()
                        handle.detach()
            if count != entity.row_count:
                raise ValueError("streamed row count mismatch")
            actual_bytes += path.stat().st_size
            counts[entity.name] = count
        report = independent_validation_report(spec)
        write_dataset_spec_artifact(spec, stage/'dataset_spec.yaml')
        if profile is not None:
            write_dataset_profile_artifact(profile, stage/'profile.json')
        write_dataset_validation_report(report, stage)
        write_json_artifact({'engine': 'scalable-v1', 'rows': sum(counts.values()),
            'generation_and_validation_seconds': generation_seconds, 'writing_seconds': writing_seconds,
            'task_generation_seconds': task_generation_seconds, 'task_validation_seconds': task_validation_seconds,
            'task_count': task_count,
            'elapsed_seconds': time.monotonic()-started, 'dataset_bytes': actual_bytes,
            'process_tree_peak_upper_bound_bytes': resident_high_water_bytes()+peak_workers}, stage/'generation_statistics.json')
        if before_publish is not None:
            before_publish(stage, report)
        write_generation_manifest(spec, seed=seed, output_format=spec.generation_settings.output_format,
            row_counts=counts, validation_valid=True, output_folder=stage)
        enforce_output_folder_size(stage)
        size = sum(p.stat().st_size for p in stage.iterdir() if p.is_file())
        if size > min(policy.max_output_bytes, policy.max_temporary_bytes):
            raise GenerationLimitError("bundle exceeds output or temporary-disk policy")
        budget.check("scalable publication")
        publish_directory(stage, output_folder, overwrite=overwrite)
        if progress is not None:
            progress(GenerationProgress(spec_sha256=fingerprint, phase='completed', rows_completed=total_rows,
                rows_total=total_rows, elapsed_seconds=time.monotonic()-started,
                remaining_seconds_low=0, remaining_seconds_high=0))
    except BaseException:
        discard_staging_directory(stage)
        raise
    return DatasetGenerationResult(seed=seed, output_format=spec.generation_settings.output_format,
        mode=spec.generation_settings.mode, row_counts=counts, validation=report)


def independent_validation_report(spec: DatasetSpec) -> DatasetValidationReport:
    """Canonical successful report after every batch and global identifier proof passed."""
    settings = spec.validation_settings.model_copy(deep=True)
    sections = []
    for name, enabled in [('schema', settings.validate_schema), ('relationships', settings.validate_relationships),
                          ('constraints', settings.validate_constraints), ('privacy', settings.validate_privacy)]:
        if enabled:
            sections.append(ValidationSection(name=name, passed=0 if name == 'relationships' else 1,
                checked=0 if name == 'relationships' else None,
                relationship_metrics=[] if name == 'relationships' else None))
    return DatasetValidationReport(valid=True, settings=settings, sections=sections,
        utility=ValidationUtilityEvidence(spec_sha256=model_fingerprint(spec), active_relationships=0,
            relationship_checks='not_declared', active_temporal_constraints=0, temporal_checks='not_declared'))
