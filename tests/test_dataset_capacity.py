"""Fictional capacity and scalable execution acceptance."""
from __future__ import annotations
import json
import multiprocessing
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.execution_policy import GenerationExecutionPolicy
from test_data_agent.generation.capacity import estimate_capacity
from test_data_agent.io.capacity import estimate_dataset_capacity
from test_data_agent.io.workflows import generate_dataset_bundle


def spec(count: int = 37, *, workers: int = 1, batch: int = 11, fmt: str = 'csv') -> DatasetSpec:
    return DatasetSpec.model_validate({'entities': [{'name': 'widgets', 'row_count': count,
        'primary_key': 'widget_id', 'fields': [
            {'name': 'widget_id', 'data_type': 'integer', 'is_identifier': True},
            {'name': 'label', 'data_type': 'string'},
            {'name': 'enabled', 'data_type': 'boolean', 'nullable': True, 'null_ratio': .3}]}],
        'generation_settings': {'seed': 12, 'output_format': fmt,
            'execution_policy': {'workers': workers, 'batch_size': batch}}})


@pytest.mark.parametrize('fmt', ['csv', 'json', 'parquet'])
def test_scalable_worker_and_batch_independent(tmp_path: Path, fmt: str) -> None:
    paths = []
    for workers, batch in [(1, 11), (2, 7), (4, 9)]:
        path = tmp_path/f'{workers}'
        result = generate_dataset_bundle(spec(workers=workers, batch=batch, fmt=fmt), output_folder=path)
        assert result.row_counts == {'widgets': 37}
        assert result.validation.valid
        manifest = json.loads((path/'generation_manifest.json').read_text())
        assert manifest['generation_execution']['engine'] == 'scalable-v1'
        paths.append(path/f'widgets.{fmt}')
    if fmt == 'parquet':
        pq = pytest.importorskip('pyarrow.parquet')
        rows = [pq.read_table(path).to_pylist() for path in paths]
        assert rows[0] == rows[1] == rows[2]
    else:
        assert paths[0].read_bytes() == paths[1].read_bytes() == paths[2].read_bytes()
    assert not multiprocessing.active_children()


def test_distinct_rows_and_no_batch_repeat(tmp_path: Path) -> None:
    generate_dataset_bundle(spec(101, batch=7, fmt='json'), output_folder=tmp_path/'out')
    rows = json.loads((tmp_path/'out/widgets.json').read_text())
    assert len({r['widget_id'] for r in rows}) == len(rows) == 101


def test_finite_limits_failure_keeps_existing_output(tmp_path: Path) -> None:
    data = spec()
    data.generation_settings.execution_policy = GenerationExecutionPolicy(max_output_bytes=10)
    existing = tmp_path/'out'
    existing.mkdir()
    (existing/'keep').write_text('original')
    with pytest.raises(ValueError, match='policy'):
        generate_dataset_bundle(data, output_folder=existing, overwrite=True)
    assert (existing/'keep').read_text() == 'original'
    assert list(tmp_path.iterdir()) == [existing]


def test_large_request_needs_explicit_policy(tmp_path: Path) -> None:
    data = spec(100001)
    data.generation_settings.execution_policy = None
    with pytest.raises(ValueError, match='row_count'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('seed', [-1, 2**63, True, 15])
def test_streamed_entrypoint_binds_bounded_seed_before_output(tmp_path: Path, seed: int) -> None:
    from test_data_agent.io.scalable import generate_scalable_bundle
    with pytest.raises(ValueError, match='seed'):
        generate_scalable_bundle(spec(), output_folder=tmp_path/'out', seed=seed)
    assert not list(tmp_path.iterdir())


def test_cli_forecast_reports_large_run_remedy_without_generation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from test_data_agent.cli import main
    from test_data_agent.io.artifacts import write_dataset_spec_artifact
    data = spec(750000)
    data.generation_settings.execution_policy = None
    path = tmp_path/'dataset_spec.yaml'
    write_dataset_spec_artifact(data, path)
    assert main(['estimate-capacity', str(path), '--database', 'postgresql', '--json']) == 0
    captured = capsys.readouterr()
    forecast = json.loads(captured.out)
    assert captured.err == ''
    assert forecast['duration_seconds'] is None
    assert forecast['postgres_table_bytes']['expected'] > 0
    assert 'execution_policy' in forecast['budget_findings'][0]
    assert list(tmp_path.iterdir()) == [path]


def test_policy_checks_total_cells_and_distinct_domain(tmp_path: Path) -> None:
    data = spec()
    data.generation_settings.execution_policy = GenerationExecutionPolicy(max_cells=10)
    with pytest.raises(ValueError, match='cells'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    data.generation_settings.execution_policy = GenerationExecutionPolicy()
    data.entities[0].primary_key = None
    with pytest.raises(ValueError, match='distinct scalable rows'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')


@pytest.mark.parametrize('name', ['generation_statistics', 'Generation_Statistics', 'Generation_Manifest'])
def test_control_artifacts_cannot_replace_dataset_files(tmp_path: Path, name: str) -> None:
    data = spec(fmt='json')
    data.entities[0].name = name
    with pytest.raises(ValueError, match='reserved'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_case_colliding_entities_reject_before_output(tmp_path: Path) -> None:
    data = spec()
    data.entities.append(data.entities[0].model_copy(update={'name': 'Widgets'}, deep=True))
    with pytest.raises(ValueError, match='distinct ignoring case'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_metadata_forecast_has_no_io_and_separates_database() -> None:
    data = spec(750000)
    report = estimate_capacity(data, database='postgresql')
    assert report.entities[0].rows == 750000
    assert report.file_bytes.expected != report.logical_database_bytes.expected
    assert report.postgres_table_bytes is not None
    assert report.duration_seconds is None
    assert report.method == 'metadata'
    assert 'scalable-v1' not in report.model_dump_json()  # no source spec payload


def test_typed_policy_is_counted_in_canonical_mcp_budget() -> None:
    from test_data_agent.trino_work_budget import canonical_argument_size
    def call(execution_policy: GenerationExecutionPolicy) -> None:
        pass
    policy = GenerationExecutionPolicy(workers=4)
    expected = json.dumps({'execution_policy': policy.model_dump(mode='json')},
        ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')
    assert canonical_argument_size(call, policy) == len(expected)
    with pytest.raises(TypeError):
        canonical_argument_size(call, object())


@pytest.mark.parametrize('fmt', ['csv', 'json', 'parquet'])
def test_calibration_is_opt_in_and_does_not_publish(tmp_path: Path, fmt: str) -> None:
    data = spec(100, fmt=fmt)
    before = data.model_dump_json()
    report = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path, use_cache=False)
    assert report.duration_seconds is not None
    assert report.method == 'synthetic_calibration'
    assert report.file_bytes.low <= report.file_bytes.expected <= report.file_bytes.high
    assert data.model_dump_json() == before
    assert not list(tmp_path.iterdir())


def test_calibration_failure_is_fixed_and_cleans(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    original = subprocess.Popen.communicate
    def fail(self: subprocess.Popen[str], *args: object, **kwargs: object) -> tuple[str, str | None]:
        if kwargs.get('timeout'):
            raise subprocess.TimeoutExpired('fixture', 30)
        return original(self)
    monkeypatch.setattr(subprocess.Popen, 'communicate', fail)
    with pytest.raises(ValueError, match='calibration'):
        estimate_dataset_capacity(spec(), calibrate=True, workspace=tmp_path)


def test_legacy_load_calibration_uses_effective_sample_count(tmp_path: Path) -> None:
    data = spec(100, fmt='json')
    data.generation_settings.execution_policy = None
    data.generation_settings.mode = 'load_test'
    data.generation_settings.load_multiplier = 100
    report = estimate_dataset_capacity(data, calibrate=True, sample_rows=1000, workspace=tmp_path, use_cache=False)
    output = tmp_path/'out'
    generate_dataset_bundle(data, output_folder=output)
    size = (output/'widgets.json').stat().st_size
    assert report.entities[0].rows == 10000
    assert report.file_bytes.low <= size <= report.file_bytes.high
    assert abs(report.file_bytes.expected-size)/size <= .25


def test_cache_reuses_only_numbers_and_invalidates_policy(tmp_path: Path) -> None:
    data = spec(100)
    first = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path)
    cache = tmp_path/'.apa-capacity-measurement.json'
    payload = json.loads(cache.read_text())
    payload['estimate']['assumptions'] = ['fictional-private-marker@example.com']
    payload['estimate']['calibration'] = {'unsafe': 'fictional-private-marker@example.com'}
    cache.write_text(json.dumps(payload))
    second = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path)
    assert second.calibration is not None and second.calibration['cache'] == 'hit'
    assert second.file_bytes == first.file_bytes
    assert 'fictional-private-marker' not in second.model_dump_json()
    data.generation_settings.execution_policy = GenerationExecutionPolicy(workers=2)
    third = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path)
    assert third.calibration is not None and third.calibration.get('cache') != 'hit'


def test_postgres_page_formula_and_wide_values_unknown() -> None:
    data = DatasetSpec.model_validate({'entities': [{'name': 'flags', 'row_count': 10,
        'fields': [{'name': 'flag', 'data_type': 'boolean'}]}]})
    report = estimate_capacity(data, database='postgresql')
    assert report.logical_database_bytes.expected == 10
    assert report.postgres_table_bytes is not None
    assert report.postgres_table_bytes.expected == 8192
    data.entities[0].fields[0].data_type = 'string'
    data.entities[0].fields[0].distribution = {'kind': 'string_pattern', 'min_length': 2000, 'max_length': 3000}
    report = estimate_capacity(data, database='postgresql')
    assert report.postgres_table_bytes is None
    oversized = spec()
    oversized.generation_settings.seed = 2**63-1
    assert estimate_capacity(oversized, database='postgresql').postgres_table_bytes is None


def test_progress_is_informational_until_publication(tmp_path: Path) -> None:
    from test_data_agent.core.generation_progress import GenerationProgress
    events: list[GenerationProgress] = []
    output = tmp_path/'out'
    def on_progress(progress: GenerationProgress) -> None:
        assert output.exists() == (progress.phase == 'completed')
        events.append(progress)
    generate_dataset_bundle(spec(), output_folder=output, progress=on_progress)
    assert events[-1].phase == 'completed'
    assert events[-1].rows_completed == 37
    assert events[-1].remaining_seconds_high == 0


def test_scoped_field_policy_cache_does_not_survive_mutation() -> None:
    from test_data_agent.safety import validate_generated_row_privacy
    data = spec()
    data.entities[0].fields[1].name = 'display_value'
    rows = {'widgets': [{'widget_id': 1, 'display_value': 'ordinary', 'enabled': True}]}
    assert not validate_generated_row_privacy(rows, data)
    data.entities[0].fields[1].sensitive = True
    assert validate_generated_row_privacy(rows, data)


@pytest.mark.parametrize('fmt', ['csv', 'json', 'parquet'])
def test_streaming_validation_uses_generation_not_source_cell_limits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fmt: str) -> None:
    from test_data_agent.io.scalable_validation import validate_scalable_bundle
    data = spec(57, fmt=fmt)
    output = tmp_path/'out'
    generated = generate_dataset_bundle(data, output_folder=output)
    monkeypatch.setenv('TEST_DATA_AGENT_MAX_INPUT_CELLS', '4')
    assert validate_scalable_bundle(data, output) == generated.validation


def test_failed_worker_and_timeout_reap_children(tmp_path: Path) -> None:
    data = spec(workers=2)
    data.generation_settings.locale = '_fictional_invalid_'
    with pytest.raises(ValueError, match='worker'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not (tmp_path/'out').exists()
    assert not multiprocessing.active_children()
    data.generation_settings.locale = None
    data.generation_settings.execution_policy = GenerationExecutionPolicy(workers=2, max_seconds=.000001)
    with pytest.raises(ValueError, match='budget'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not multiprocessing.active_children()
    assert not list(tmp_path.iterdir())


def test_serial_batches_share_the_parent_deadline() -> None:
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.io.scalable import _batches
    ticks = iter(range(1000))
    budget = GenerationBudget(3, clock=lambda: next(ticks))
    with pytest.raises(ValueError, match='scalable row generation'):
        list(_batches(spec(), 0, 12, budget))


def test_disk_failure_never_publishes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_data_agent.io.scalable import _LimitedWriter
    def fail(self: object, data: object) -> int:
        raise OSError('fictional-disk-full')
    monkeypatch.setattr(_LimitedWriter, 'write', fail)
    with pytest.raises(OSError):
        generate_dataset_bundle(spec(workers=2), output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())
    assert not multiprocessing.active_children()


def test_json_writer_and_reader_share_bounded_row_size(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    import test_data_agent.io.scalable as writer
    import test_data_agent.io.scalable_validation as reader
    monkeypatch.setattr(writer, 'MAX_SCALABLE_JSON_ROW_CHARS', 16)
    monkeypatch.setattr(reader, 'MAX_SCALABLE_JSON_ROW_CHARS', 16)
    with pytest.raises(ValueError, match='decode size'):
        generate_dataset_bundle(spec(fmt='json'), output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match='decode size'):
        list(reader._json_rows(io.StringIO('[{"value":"fictional-long-marker"}]')))


def test_multiple_tables_keep_scoped_privacy_and_disjoint_keys(tmp_path: Path) -> None:
    from test_data_agent.io.scalable_validation import validate_scalable_bundle
    data = spec(101, workers=2, fmt='json')
    other = data.entities[0].model_copy(update={'name': 'gadgets'}, deep=True)
    other.fields[0].sensitive = True
    data.entities.append(other)
    data.privacy_rules = [{'entity': 'gadgets', 'field': 'widget_id', 'action': 'synthetic'}]
    output = tmp_path/'out'
    generate_dataset_bundle(data, output_folder=output)
    assert validate_scalable_bundle(data, output).valid
    first = json.loads((output/'widgets.json').read_text())
    second = json.loads((output/'gadgets.json').read_text())
    assert not {row['widget_id'] for row in first} & {row['widget_id'] for row in second}
    estimate = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path, use_cache=False)
    assert estimate.duration_seconds is not None


def test_cancellation_reaps_children_and_cleans_staging(tmp_path: Path) -> None:
    def cancel(progress: object) -> None:
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        generate_dataset_bundle(spec(100, workers=2), output_folder=tmp_path/'out', progress=cancel)
    assert not list(tmp_path.iterdir())
    assert not multiprocessing.active_children()


@pytest.mark.parametrize('mode', ['negative', 'mixed', 'load_test'])
def test_scalable_unsupported_modes_reject_before_output(tmp_path: Path, mode: str) -> None:
    data = spec()
    data.generation_settings.mode = mode
    with pytest.raises(ValueError, match='valid and edge'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_linked_tables_reject_scalable_but_keep_legacy_path(tmp_path: Path) -> None:
    from test_data_agent.core.relationship import Relationship
    data = spec(20)
    data.entities.append(data.entities[0].model_copy(update={'name': 'gadgets'}, deep=True))
    data.relationships.append(Relationship(parent_entity='widgets', parent_field='widget_id',
        child_entity='gadgets', child_field='widget_id', relationship_type='one_to_one',
        confidence=1, status='confirmed'))
    with pytest.raises(ValueError, match='independent tables'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    estimate = estimate_dataset_capacity(data, calibrate=True, workspace=tmp_path)
    assert estimate.duration_seconds is None
    assert not list(tmp_path.iterdir())
    data.generation_settings.execution_policy = None
    assert generate_dataset_bundle(data, output_folder=tmp_path/'legacy').validation.valid


@pytest.mark.parametrize('tampering', ['key', 'privacy', 'extra_file'])
def test_streamed_revalidation_checks_values_and_inventory(tmp_path: Path, tampering: str) -> None:
    import hashlib
    from test_data_agent.io.scalable_validation import validate_scalable_bundle
    data = spec(20, fmt='json')
    output = tmp_path/'out'
    generate_dataset_bundle(data, output_folder=output)
    if tampering == 'extra_file':
        (output/'untracked.txt').write_text('fictional')
    else:
        path = output/'widgets.json'
        rows = json.loads(path.read_text())
        if tampering == 'key':
            rows[0]['widget_id'] = rows[1]['widget_id']
        else:
            rows[0]['label'] = 'fictional-person@example.com'
        path.write_text(json.dumps(rows))
        manifest_path = output/'generation_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['reproducibility']['output_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError) as caught:
        validate_scalable_bundle(data, output)
    assert 'fictional-person' not in str(caught.value)
