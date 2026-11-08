"""Opt-in, bounded synthetic calibration around the pure capacity forecast."""
from __future__ import annotations

import json
import hashlib
import platform
import importlib.metadata
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.capacity import CapacityEstimate, estimate_capacity, spread, total
from test_data_agent.safety import assert_spec_safe


def _budget_findings(spec: DatasetSpec, estimate: CapacityEstimate) -> list[str]:
    from test_data_agent.core.limits import max_generation_count
    policy = spec.generation_settings.execution_policy
    findings = []
    if policy is None:
        if any(e.rows > max_generation_count() for e in estimate.entities):
            findings.append(f"Requested rows exceed the legacy per-table cap {max_generation_count()}; review an explicit execution_policy for supported independent-table streaming.")
    else:
        if sum(e.rows for e in estimate.entities) > policy.max_rows:
            findings.append("Total rows exceed execution_policy.max_rows; reduce counts or review a larger finite policy.")
        if sum(e.cells for e in estimate.entities) > policy.max_cells:
            findings.append("Total cells exceed execution_policy.max_cells; reduce rows/columns or review a larger finite policy.")
        if estimate.file_bytes.high > min(policy.max_output_bytes, policy.max_temporary_bytes):
            findings.append("Forecast high bytes exceed output or temporary-disk policy; calibrate and review disk budgets. Actual byte limits remain authoritative.")
    return findings


def estimate_dataset_capacity(spec: DatasetSpec, *, database: Literal['logical', 'postgresql'] = 'logical',
                              calibrate: bool = False, sample_rows: int = 2000,
                              workspace: Path | None = None, use_cache: bool = True) -> CapacityEstimate:
    assert_spec_safe(spec)
    if len(spec.entities) > 100 or sum(len(e.fields) for e in spec.entities) > 10_000:
        raise ValueError("capacity estimation exceeds bounded schema size")
    estimate = estimate_capacity(spec, database=database)
    estimate.budget_findings = _budget_findings(spec, estimate)
    if not calibrate:
        return estimate
    if not 100 <= sample_rows <= 5000:
        raise ValueError('calibration sample_rows must be between 100 and 5000')
    if sum(min(sample_rows, e.rows)*len(spec.entity(e.entity).fields) for e in estimate.entities) > 200_000:
        raise ValueError('calibration exceeds 200000-cell budget; reduce sample_rows')
    if spec.relationships or spec.constraints or spec.business_rules or spec.relational_scenarios:
        estimate.duration_unknown_reason = 'Calibration of related or rule-constrained datasets is not supported; use a representative offline benchmark.'
        return estimate
    cache_path = workspace / '.apa-capacity-measurement.json' if workspace is not None and use_cache else None
    try:
        dependencies = {name: importlib.metadata.version(name)
            for name in (('agent-paranoid-android', 'Faker', 'pydantic', 'pyarrow') if estimate.output_format == 'parquet' else ('agent-paranoid-android', 'Faker', 'pydantic'))}
    except importlib.metadata.PackageNotFoundError:
        raise ValueError('synthetic calibration requires the installed package and format dependencies; install the parquet extra for Parquet') from None
    cache_key = hashlib.sha256(json.dumps({
        'spec': estimate.spec_sha256, 'rows': sample_rows, 'database': database, 'estimator': '1',
        'machine': platform.node(), 'architecture': platform.machine(), 'cpus': os.cpu_count(),
        'python': sys.version, 'dependencies': dependencies,
    }, sort_keys=True).encode()).hexdigest()
    cache_writable = cache_path is not None
    if cache_path is not None and cache_path.exists():
        from test_data_agent.core.limits import read_limited_text
        try:
            cached = json.loads(read_limited_text(cache_path, max_bytes=128*1024))
            cache_writable = cached.get('artifact_type') == 'capacity_calibration_v1'
            age = time.time()-float(cached.get('created', 0))
            if cache_writable and cached.get('key') == cache_key and 0 <= age < 3600:
                previous = CapacityEstimate.model_validate(cached['estimate'])
                if previous.spec_sha256 != estimate.spec_sha256 or previous.output_format != estimate.output_format:
                    raise ValueError("calibration cache identity mismatch")
                # Local artifacts are untrusted: reuse numeric measurements only,
                # never cached strings, names, assumptions or free-form metadata.
                for current, old in zip(estimate.entities, previous.entities, strict=True):
                    current.file_bytes = old.file_bytes
                estimate.file_bytes = total([entity.file_bytes for entity in estimate.entities])
                estimate.duration_seconds = previous.duration_seconds
                estimate.duration_unknown_reason = None if previous.duration_seconds is not None else estimate.duration_unknown_reason
                estimate.duration_stages_seconds = {name: value for name, value in previous.duration_stages_seconds.items()
                    if name in {'generation', 'validation', 'writing', 'setup_publication', 'end_to_end'}}
                estimate.method = 'synthetic_calibration'
                estimate.confidence = 'medium'
                estimate.calibration = {'cache': 'hit', 'sample_rows_per_entity': sample_rows}
                estimate.budget_findings = _budget_findings(spec, estimate)
                return estimate
        except (OSError, ValueError, KeyError):
            cache_writable = False
    sample = spec.model_copy(deep=True)
    effective_counts = {entity.entity: entity.rows for entity in estimate.entities}
    for entity in sample.entities:
        entity.row_count = min(effective_counts[entity.name], sample_rows)
    sample.generation_settings.load_multiplier = 1
    policy = sample.generation_settings.execution_policy
    if policy is not None:
        sample.generation_settings.execution_policy = policy.model_copy(update={
            "max_output_bytes": min(policy.max_output_bytes, 16*1024**2),
            "max_temporary_bytes": min(policy.max_temporary_bytes, 16*1024**2),
            "max_seconds": min(policy.max_seconds, 25.)})
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='apa-capacity-', dir=workspace) as folder:
        from test_data_agent.trino_work_budget import current_query_work_budget
        request_budget = current_query_work_budget()
        timeout = min(30., request_budget.remaining_invocation_seconds()) if request_budget is not None else 30.
        env = dict(os.environ)
        from test_data_agent.core.limits import max_output_bytes
        env['TEST_DATA_AGENT_MAX_OUTPUT_BYTES'] = str(min(max_output_bytes(), 16*1024**2))
        process = subprocess.Popen([sys.executable, '-m', 'test_data_agent.io.capacity', folder], env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, start_new_session=True)
        try:
            stdout, _ = process.communicate(sample.model_dump_json(), timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise ValueError('bounded synthetic calibration interrupted or exceeded 30 seconds') from None
        if process.returncode:
            raise ValueError('bounded synthetic calibration failed; check specification, optional dependencies or execution policy')
        result = json.loads(stdout)
    times = []
    stages: dict[str, float] = {}
    for predicted in estimate.entities:
        measured = result['entities'][predicted.entity]
        sample_count = min(predicted.rows, sample_rows)
        size = measured['bytes']*predicted.rows/max(1, sample_count)
        predicted.file_bytes = spread(size, .7, 1.4)
        ratio = predicted.rows/max(1, sample_count)
        if 'task_seconds' in measured:
            workers = spec.generation_settings.execution_policy.workers if spec.generation_settings.execution_policy else 1
            active = min(workers, measured['task_count'])
            fixed = max(0., measured['seconds']-measured['task_seconds']/max(1, active)-measured['writing_seconds'])
            times.append(fixed + ratio*(measured['task_seconds']/workers+measured['writing_seconds']))
            for key, amount in {'setup_publication': fixed, 'generation': ratio*measured['generation_seconds']/workers,
                                'validation': ratio*measured['validation_seconds']/workers,
                                'writing': ratio*measured['writing_seconds']}.items():
                stages[key] = stages.get(key, 0.)+amount
        else:
            setup = measured['format_setup_seconds']
            elapsed = setup+(measured['seconds']-setup)*ratio
            times.append(elapsed)
            stages['end_to_end'] = stages.get('end_to_end', 0.)+elapsed
    estimate.file_bytes = total([e.file_bytes for e in estimate.entities])
    estimate.budget_findings = _budget_findings(spec, estimate)
    estimate.duration_seconds = spread(sum(times), .65, 1.5)
    estimate.duration_stages_seconds = {name: spread(value, .65, 1.5) for name, value in stages.items()}
    estimate.calibration_seconds = time.monotonic()-started
    estimate.duration_unknown_reason = None
    estimate.method = 'synthetic_calibration'
    estimate.confidence = 'medium'
    estimate.calibration = {'sample_rows_per_entity': sample_rows, 'python': sys.version.split()[0],
        'workers': sample.generation_settings.execution_policy.workers if sample.generation_settings.execution_policy else 1,
        'seconds': estimate.calibration_seconds}
    estimate.assumptions += ['Calibration includes generation, safety validation, serialization and publication; same machine and engine required.',
        'Sample extrapolation can be optimistic for global state, compression, CPU contention and storage saturation.']
    if cache_path is not None and cache_writable:
        from test_data_agent.io.artifacts import write_json_artifact
        write_json_artifact({'artifact_type': 'capacity_calibration_v1', 'key': cache_key,
            'created': time.time(), 'estimate': estimate.model_dump(mode='json')}, cache_path)
    return estimate


def _calibrate(folder: Path, spec: DatasetSpec) -> None:
    from test_data_agent.io.workflows import generate_dataset_bundle
    result = {}
    format_setup_seconds = 0.
    if spec.generation_settings.output_format == 'parquet':
        started = time.monotonic()
        import pyarrow.parquet  # noqa: F401
        format_setup_seconds = time.monotonic()-started
    # All sample output remains private, synthetic and temporary. No rows leave this process.
    for index, entity in enumerate(spec.entities):
        sample = spec.model_copy(update={
            'entities': [entity],
            'privacy_rules': [rule for rule in spec.privacy_rules if rule.entity in (None, entity.name)],
            'local_category_fields': [field for field in spec.local_category_fields if field.entity == entity.name],
        }, deep=True)
        started = time.monotonic()
        output = folder/str(index)
        generate_dataset_bundle(sample, output_folder=output)
        path = output/(entity.name+'.'+sample.generation_settings.output_format.value)
        record = {'seconds': time.monotonic()-started+format_setup_seconds,
                  'format_setup_seconds': format_setup_seconds, 'bytes': path.stat().st_size}
        format_setup_seconds = 0.
        statistics = output/'generation_statistics.json'
        if statistics.exists():
            stats = json.loads(statistics.read_text())
            record.update(task_seconds=stats['task_generation_seconds']+stats['task_validation_seconds'],
                          task_count=stats['task_count'], writing_seconds=stats['writing_seconds'],
                          generation_seconds=stats['task_generation_seconds'], validation_seconds=stats['task_validation_seconds'])
        result[entity.name] = record
        # Only one bounded sample bundle exists at a time, even for many entities.
        from test_data_agent.io.path_policy import discard_staging_directory
        discard_staging_directory(output)
    print(json.dumps({'entities': result}))


if __name__ == '__main__':
    _calibrate(Path(sys.argv[1]).resolve(), DatasetSpec.model_validate_json(sys.stdin.read()))
