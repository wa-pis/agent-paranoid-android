"""Fictional linked-table scale contracts."""
from __future__ import annotations

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.generation.relational import plan_relational_spec


def linked_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({'entities': [
        {'name': name, 'row_count': count, 'primary_key': name+'_id', 'fields': [
            {'name': name+'_id', 'data_type': 'integer', 'is_identifier': True},
            *([{'name': parent+'_id', 'data_type': 'integer', 'is_identifier': True}] if parent else []),
            {'name': 'label', 'data_type': 'string'}]}
        for name, count, parent in [('lines', 43, 'orders'), ('people', 17, None), ('orders', 29, 'people')]],
        'relationships': [
            {'parent_entity': 'people', 'parent_field': 'people_id', 'child_entity': 'orders', 'child_field': 'people_id', 'confidence': 1},
            {'parent_entity': 'orders', 'parent_field': 'orders_id', 'child_entity': 'lines', 'child_field': 'orders_id', 'confidence': 1}],
        'generation_settings': {'seed': 42}})


def test_stable_parent_first_order_preserves_original_entity_indices() -> None:
    data = linked_spec()
    plan = plan_relational_spec(data, budget=GenerationBudget())
    assert plan.entity_order == (1, 2, 0)
    assert [link.parent_entity for link in plan.incoming[0]] == ['orders']


def test_graph_rejection_and_budget_admission() -> None:
    data = linked_spec()
    data.relationships[0].parent_field = 'label'
    with pytest.raises(ValueError, match='primary key'):
        plan_relational_spec(data, budget=GenerationBudget())
    data = linked_spec()
    from test_data_agent.core.relationship import RelationshipType
    data.relationships[0].relationship_type = RelationshipType.ONE_TO_ONE
    with pytest.raises(ValueError, match='sufficient'):
        plan_relational_spec(data, budget=GenerationBudget())
    data = linked_spec()
    data.entities.extend(data.entities * 34)
    with pytest.raises(GenerationLimitError, match='graph exceeds'):
        plan_relational_spec(data, budget=GenerationBudget())


def test_rejected_hypotheses_do_not_create_dependencies() -> None:
    data = linked_spec()
    for relationship in data.relationships:
        relationship.status = 'rejected'
    plan = plan_relational_spec(data, budget=GenerationBudget())
    assert plan.entity_order == (0, 1, 2)
    assert not any(plan.incoming)


def execution_spec(*, workers: int = 1, batch: int = 11, fmt: str = 'json') -> DatasetSpec:
    from test_data_agent.core.execution_policy import GenerationExecutionPolicy
    data = linked_spec()
    data.generation_settings.output_format = fmt
    data.generation_settings.execution_policy = GenerationExecutionPolicy(
        # The coverage runner retains earlier tests' RSS high-water; benchmarks
        # separately verify fresh-process generation under the default 1 GiB.
        engine='scalable-relational-v1', workers=workers, batch_size=batch, max_memory_bytes=4*1024**3)
    return data


@pytest.mark.parametrize('fmt', ['csv', 'json', 'parquet'])
def test_streamed_chain_determinism_and_executed_recovery(tmp_path, fmt) -> None:
    import json
    import multiprocessing
    from test_data_agent.io.scalable_validation import _rows, validate_scalable_bundle
    from test_data_agent.io.workflows import generate_dataset_bundle
    from test_data_agent.core.settings import OutputFormat
    versions = []
    for workers, batch in [(1, 11), (2, 7), (4, 9)]:
        data = execution_spec(workers=workers, batch=batch, fmt=fmt)
        field = data.entity("orders").field("people_id")
        field.nullable = True
        field.null_ratio = .35
        folder = tmp_path / str(workers)
        result = generate_dataset_bundle(data, output_folder=folder)
        assert validate_scalable_bundle(data, folder) == result.validation
        assert result.validation.utility.relationship_checks == 'executed'
        metrics = next(s for s in result.validation.sections if s.name == 'relationships').relationship_metrics
        assert metrics[0].checked_references == metrics[0].resolved_references
        assert metrics[0].checked_references + metrics[0].null_references == 29
        assert metrics[0].null_references > 0
        assert metrics[1].checked_references == metrics[1].resolved_references == 43
        rows = {e.name: list(_rows(folder / f'{e.name}.{fmt}', OutputFormat(fmt), [f.name for f in e.fields], 7)) for e in data.entities}
        for parent, child in [('people', 'orders'), ('orders', 'lines')]:
            assert {r[parent+'_id'] for r in rows[child] if r[parent+'_id'] is not None} <= {r[parent+'_id'] for r in rows[parent]}
        assert json.loads((folder/'generation_statistics.json').read_text())['engine'] == 'scalable-relational-v1'
        versions.append(rows)
    assert versions[0] == versions[1] == versions[2]
    assert not multiprocessing.active_children()


def test_nullable_string_one_to_one_and_multiple_parents(tmp_path) -> None:
    from test_data_agent.io.workflows import generate_dataset_bundle
    from test_data_agent.io.scalable_validation import validate_scalable_bundle
    import json
    data = execution_spec()
    data.entities[1].row_count = 37
    for entity in data.entities:
        for field in entity.fields:
            if field.is_identifier:
                field.data_type = 'string'
    from test_data_agent.core.relationship import RelationshipType
    data.relationships[0].relationship_type = RelationshipType.ONE_TO_ONE
    foreign = data.entity('orders').field('people_id')
    foreign.nullable = True
    foreign.null_ratio = .5
    # A second parent for lines, in addition to orders.
    from test_data_agent.core.field import FieldSpec
    from test_data_agent.core.relationship import Relationship
    data.entity('lines').fields.append(FieldSpec(name='people_id', data_type='string'))
    data.relationships.append(Relationship(parent_entity='people', parent_field='people_id',
        child_entity='lines', child_field='people_id', confidence=1))
    data.validation_settings.validate_relationships = False
    folder = tmp_path/'out'
    result = generate_dataset_bundle(data, output_folder=folder)
    assert validate_scalable_bundle(data, folder) == result.validation
    metrics = next(s for s in result.validation.sections if s.name == 'relationships').relationship_metrics
    assert 0 < metrics[0].null_references < 29
    assert metrics[0].checked_references + metrics[0].null_references == 29
    orders = json.loads((folder/'orders.json').read_text())
    keys = [r['people_id'] for r in orders if r['people_id'] is not None]
    assert len(set(keys)) == len(keys)


@pytest.mark.parametrize('tampering', ['foreign_key', 'primary_key', 'null'])
def test_recovery_rejects_rehashed_key_tampering(tmp_path, tampering) -> None:
    import hashlib
    import json
    from test_data_agent.io.scalable_validation import validate_scalable_bundle
    from test_data_agent.io.workflows import generate_dataset_bundle
    data = execution_spec()
    data.validation_settings.validate_relationships = False
    folder = tmp_path/'out'
    generate_dataset_bundle(data, output_folder=folder)
    path = folder/'orders.json'
    rows = json.loads(path.read_text())
    if tampering == 'foreign_key':
        parents = json.loads((folder/'people.json').read_text())
        rows[0]['people_id'] = next(r['people_id'] for r in parents if r['people_id'] != rows[0]['people_id'])
    elif tampering == 'primary_key':
        rows[0]['orders_id'] = rows[1]['orders_id']
    else:
        rows[0]['people_id'] = None
    path.write_text(json.dumps(rows))
    manifest_path = folder/'generation_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['reproducibility']['output_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        validate_scalable_bundle(data, folder)


@pytest.mark.parametrize('failure', ['cancel', 'bad_reference'])
def test_late_child_failure_keeps_existing_bundle_and_reaps(tmp_path, failure) -> None:
    import multiprocessing
    from test_data_agent.io.scalable import generate_scalable_bundle
    data = execution_spec(workers=2)
    folder = tmp_path/'out'
    folder.mkdir()
    (folder/'keep').write_text('fictional original')
    seen = []
    def check(values):
        seen.extend(values)
        if 'lines' in values:
            if failure == 'cancel':
                raise KeyboardInterrupt('fictional cancellation')
            values['lines'][0]['orders_id'] = -1
    with pytest.raises((KeyboardInterrupt, ValueError)):
        generate_scalable_bundle(data, output_folder=folder, seed=42, overwrite=True, check_batch=check)
    assert 'people' in seen and 'orders' in seen
    assert (folder/'keep').read_text() == 'fictional original'
    assert list(tmp_path.iterdir()) == [folder]
    assert not multiprocessing.active_children()


def test_cycle_rejects_before_staging(tmp_path) -> None:
    from test_data_agent.core.field import FieldSpec
    from test_data_agent.core.relationship import Relationship
    from test_data_agent.io.workflows import generate_dataset_bundle
    data = execution_spec()
    data.entity('people').fields.append(FieldSpec(name='line_ref', data_type='integer'))
    data.relationships.append(Relationship(parent_entity='lines', parent_field='lines_id',
        child_entity='people', child_field='line_ref', confidence=1))
    with pytest.raises(ValueError, match='cycles'):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_relational_calibration_is_bounded_and_supported(tmp_path) -> None:
    from test_data_agent.io.capacity import estimate_dataset_capacity
    data = execution_spec()
    data.entity('people').row_count = 217
    data.entity('orders').row_count = 229
    data.entity('lines').row_count = 243
    estimate = estimate_dataset_capacity(data, calibrate=True, sample_rows=100, workspace=tmp_path)
    assert estimate.method == 'synthetic_calibration'
    assert estimate.duration_seconds is not None
    assert not list(tmp_path.glob('apa-capacity-*'))


def test_shared_deadline_covers_later_entities(tmp_path, monkeypatch) -> None:
    import test_data_agent.io.scalable as streaming
    now = [0.]
    budget = GenerationBudget(10, clock=lambda: now[0])
    monkeypatch.setattr(streaming, 'generation_budget_for_invocation', lambda **kwargs: budget)
    data = execution_spec()
    def check(values):
        if 'orders' in values:
            now[0] = 11.
    with pytest.raises(GenerationLimitError, match='budget'):
        streaming.generate_scalable_bundle(data, output_folder=tmp_path/'out', seed=42, check_batch=check)
    assert not list(tmp_path.iterdir())


def test_cli_relational_generate_and_validate(tmp_path) -> None:
    import subprocess
    import sys
    import yaml
    data = execution_spec()
    path = tmp_path/'spec.yaml'
    path.write_text(yaml.safe_dump(data.model_dump(mode='json')))
    for args in [('generate', str(path), '--output', str(tmp_path/'out')),
                 ('validate', str(tmp_path/'out/dataset_spec.yaml'), str(tmp_path/'out'))]:
        result = subprocess.run([sys.executable, '-m', 'test_data_agent.cli', *args], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('kind', ['self', 'non_pk', 'shared_pk', 'wrong_type', 'conflict', 'too_few', 'key_pool', 'load'])
def test_unsupported_graphs_reject_before_allocation(tmp_path, kind) -> None:
    from test_data_agent.io.workflows import generate_dataset_bundle
    data = execution_spec()
    link = data.relationships[0]
    if kind == 'self':
        link.child_entity, link.child_field = 'people', 'label'
    elif kind == 'non_pk':
        link.parent_field = 'label'
    elif kind == 'shared_pk':
        link.child_field = 'orders_id'
    elif kind == 'wrong_type':
        data.entity('orders').field('people_id').data_type = 'string'
    elif kind == 'conflict':
        data.relationships.append(link.model_copy(deep=True))
    elif kind == 'too_few':
        from test_data_agent.core.relationship import RelationshipType
        link.relationship_type = RelationshipType.ONE_TO_ONE
    elif kind == 'key_pool':
        data.entity('people').field('people_id').distribution = dict(kind='synthetic_identifier', pool_size=2)
    else:
        data.generation_settings.mode = 'load_test'
    with pytest.raises(ValueError):
        generate_dataset_bundle(data, output_folder=tmp_path/'out')
    assert not list(tmp_path.iterdir())


def test_capacity_does_not_certify_unsupported_relational_graph() -> None:
    from test_data_agent.io.capacity import estimate_dataset_capacity
    data = execution_spec()
    data.relationships[0].parent_field = 'label'
    forecast = estimate_dataset_capacity(data)
    assert any('not admitted' in finding for finding in forecast.budget_findings)
    calibrated = estimate_dataset_capacity(data, calibrate=True)
    assert calibrated.duration_seconds is None
    assert 'supported acyclic' in calibrated.duration_unknown_reason


def test_forecast_uses_synthetic_foreign_key_width_without_identifier_flag() -> None:
    from test_data_agent.generation.capacity import estimate_capacity
    data = execution_spec()
    foreign = data.entity('orders').field('people_id')
    expected = estimate_capacity(data).file_bytes
    foreign.is_identifier = False
    assert estimate_capacity(data).file_bytes == expected
