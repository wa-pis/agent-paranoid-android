"""Revalidate opt-in generated bundles without source/profiling allocation limits."""
from __future__ import annotations

import io
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.execution_policy import MAX_SCALABLE_JSON_ROW_CHARS
from test_data_agent.core.csv_reader import ScopedDictReader
from test_data_agent.core.limits import GenerationLimitError, output_folder_size
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.entity_generator import synthetic_identifier
from test_data_agent.generation.scalable import check_scalable_spec, resident_high_water_bytes
from test_data_agent.io.artifacts import validate_generation_bundle
from test_data_agent.io.csv_encoding import decode_csv_cell
from test_data_agent.io.path_policy import open_regular_file
from test_data_agent.io.scalable import scalable_validation_report
from test_data_agent.generation.relational import merge_relationship_metrics, validate_relational_rows
from test_data_agent.validation.relationship_validator import RelationshipMetrics
from test_data_agent.io.writers import safe_entity_artifact_path
from test_data_agent.trino_work_budget import generation_budget_for_invocation
from test_data_agent.validation.reconciliation import DatasetValidationReport, validate_dataset
from test_data_agent.core.fingerprints import model_fingerprint


def _json_rows(handle: Any) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    buffer = ''
    state = 'start'
    eof = False
    while True:
        buffer = buffer.lstrip()
        if state == 'start' and buffer.startswith('['):
            buffer = buffer[1:]
            state = 'first'
            continue
        if state in {'first', 'separator'} and buffer.startswith(']'):
            buffer = buffer[1:]
            state = 'done'
            continue
        if state == 'separator' and buffer.startswith(','):
            buffer = buffer[1:]
            state = 'row'
            continue
        if state in {'first', 'row'} and buffer.startswith('{'):
            try:
                value, end = decoder.raw_decode(buffer)
            except (ValueError, RecursionError):
                pass
            else:
                if end > MAX_SCALABLE_JSON_ROW_CHARS:
                    raise GenerationLimitError('streamed JSON row exceeds bounded decode size')
                buffer = buffer[end:]
                state = 'separator'
                yield value
                continue
        if eof:
            if state == 'done' and not buffer:
                return
            raise ValueError('invalid streamed JSON dataset')
        extra = handle.read(65536)
        eof = not extra
        buffer += extra
        if len(buffer) > MAX_SCALABLE_JSON_ROW_CHARS+65536:
            raise GenerationLimitError('streamed JSON row exceeds bounded decode buffer')


def _rows(path: Path, fmt: OutputFormat, columns: list[str], batch_size: int) -> Iterator[dict[str, Any]]:
    with open_regular_file(path) as binary:
        if fmt == OutputFormat.PARQUET:
            import pyarrow.parquet as pq
            parquet = pq.ParquetFile(binary)
            if parquet.schema_arrow.names != columns:
                raise ValueError('Parquet schema does not match reviewed fields')
            for batch in parquet.iter_batches(batch_size=batch_size):
                yield from batch.to_pylist()
        else:
            with io.TextIOWrapper(binary, encoding='utf-8', newline='') as handle:
                if fmt == OutputFormat.CSV:
                    reader = ScopedDictReader(handle)
                    if reader.fieldnames is not None:
                        reader.fieldnames = [decode_csv_cell(name) or "" for name in reader.fieldnames]
                    if reader.fieldnames != columns:
                        raise ValueError('CSV schema does not match reviewed fields')
                    for row in reader:
                        yield {name: decode_csv_cell(value) for name, value in row.items()}
                else:
                    yield from _json_rows(handle)


def validate_scalable_bundle(spec: DatasetSpec, folder: Path, *,
                             check_batch: Callable[[dict[str, list[dict[str, Any]]]], None] | None = None) -> DatasetValidationReport:
    policy = spec.generation_settings.execution_policy
    assert policy is not None
    budget = generation_budget_for_invocation(max_seconds=policy.max_seconds)
    plan = check_scalable_spec(spec, budget=budget)
    relationship_metrics: list[RelationshipMetrics] = []
    manifest = validate_generation_bundle(folder)
    if output_folder_size(folder) > policy.max_output_bytes:
        raise GenerationLimitError('scalable bundle exceeds execution-policy output bytes')
    if (manifest.spec_sha256 != model_fingerprint(spec) or manifest.generation_execution != policy.model_dump()
            or manifest.seed != (spec.generation_settings.seed or 0)
            or manifest.output_format != spec.generation_settings.output_format):
        raise ValueError('scalable bundle does not match reviewed specification or execution policy')
    required = {entity.name+'.'+manifest.output_format.value for entity in spec.entities}
    required |= {'dataset_spec.yaml', 'validation_report.json'}
    if manifest.reproducibility is None or not required <= set(manifest.reproducibility.output_sha256):
        raise ValueError('scalable bundle omits required integrity hashes')
    allowed = set(manifest.reproducibility.output_sha256) | {'generation_manifest.json'}
    if any(path.is_symlink() or not path.is_file() or path.name not in allowed for path in folder.iterdir()):
        raise ValueError('scalable bundle contains untracked artifacts')
    domains = {key: index for index, key in enumerate(sorted(
        (entity.name, field.name) for entity in spec.entities for field in entity.fields if field.is_identifier))}
    for entity_index in (plan.entity_order if plan is not None else range(len(spec.entities))):
        entity = spec.entities[entity_index]
        count = 0
        batch = []
        path = safe_entity_artifact_path(folder, entity.name, '.'+manifest.output_format.value)
        for row in _rows(path, manifest.output_format, [f.name for f in entity.fields], policy.batch_size):
            budget.check('streaming validation')
            if not isinstance(row, dict) or set(row) != {f.name for f in entity.fields}:
                raise ValueError('streamed row schema mismatch')
            if entity.primary_key is not None:
                field = entity.field(entity.primary_key)
                expected = synthetic_identifier(entity.name, field, count, manifest.seed,
                    domain=domains[(entity.name, field.name)], domain_count=max(1, len(domains)))
                if str(row.get(field.name)) != str(expected):
                    raise ValueError('streamed synthetic key range or ordering is invalid')
            count += 1
            if count > entity.row_count:
                raise ValueError('streamed row count exceeds reviewed specification')
            batch.append(row)
            if len(batch) >= policy.batch_size:
                _validate_batch(batch, entity.name, spec, check_batch, budget)
                if plan is not None:
                    merge_relationship_metrics(relationship_metrics, validate_relational_rows(
                        spec, plan, entity_index, batch, start=count-len(batch), seed=manifest.seed, budget=budget))
                batch = []
            if resident_high_water_bytes() > policy.max_memory_bytes:
                raise GenerationLimitError('streaming validation exceeded memory policy')
        if batch:
            _validate_batch(batch, entity.name, spec, check_batch, budget)
            if plan is not None:
                merge_relationship_metrics(relationship_metrics, validate_relational_rows(
                    spec, plan, entity_index, batch, start=count-len(batch), seed=manifest.seed, budget=budget))
        if count != entity.row_count or manifest.row_counts.get(entity.name) != count:
            raise ValueError('streamed row count does not match reviewed specification')
    if set(manifest.row_counts) != {e.name for e in spec.entities}:
        raise ValueError('streamed entity inventory mismatch')
    budget.check('streaming validation completion')
    return scalable_validation_report(spec, relationship_metrics)


def _validate_batch(rows: list[dict[str, Any]], name: str, spec: DatasetSpec,
                    check: Callable[[dict[str, list[dict[str, Any]]]], None] | None, budget: Any) -> None:
    entity = spec.entity(name).model_copy(update={'row_count': len(rows)})
    chunk = spec.model_copy(update={
        'entities': [entity],
        'relationships': [],
        'privacy_rules': [rule for rule in spec.privacy_rules if rule.entity in (None, name)],
        'local_category_fields': [field for field in spec.local_category_fields if field.entity == name],
    })
    # Mandatory checks also run when report options are disabled.
    from test_data_agent.core.settings import ValidationSettings
    chunk.validation_settings = ValidationSettings()
    values = {name: rows}
    if not validate_dataset(values, chunk, budget=budget).valid:
        raise ValueError('streamed dataset failed mandatory validation')
    if check is not None:
        check(values)
