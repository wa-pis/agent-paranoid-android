"""Opt-in process generation is deterministic and retains global safety checks."""

import multiprocessing
import signal
from unittest.mock import Mock

import pytest

import test_data_agent.adapters.parallel_generation as parallel
from test_data_agent.adapters.parallel_generation import (
    ParallelGenerationError,
    ParallelGenerationPolicy,
    generate_dataset_parallel,
)
from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.tiled_generator import TILE_ROWS
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation import validate_dataset
from test_data_agent.validation.reconciliation import GenerationValidationError


def diverse_spec(mode="valid"):
    fields = [
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="group_id", data_type="string", is_identifier=True,
                  nullable=True, null_ratio=0.25,
                  distribution={"kind": "synthetic_identifier", "pool_size": 3}),
        FieldSpec(name="quantity", data_type="integer",
                  distribution={"kind": "numeric", "min_value": 1, "max_value": 40}),
        FieldSpec(name="amount", data_type="float",
                  distribution={"kind": "numeric_shape", "max_abs_magnitude": 2,
                                "has_negative": True, "has_positive": True}),
        FieldSpec(name="active", data_type="boolean", nullable=True, null_ratio=0.3,
                  distribution={"kind": "boolean", "true_ratio": 0.3}),
        FieldSpec(name="day", data_type="date",
                  distribution={"kind": "date_range", "min": "2020-01-01", "max": "2025-01-01"}),
        FieldSpec(name="instant", data_type="datetime",
                  distribution={"kind": "datetime_range", "min": "2024-01-01T00:00:00+03:00",
                                "max": "2024-01-03T00:00:00+03:00"}),
        FieldSpec(name="category", data_type="string",
                  distribution={"kind": "categorical", "categories": [
                      {"value": "synthetic_синий", "count": 3},
                      {"value": "synthetic_зелёный", "count": 1}]}),
        FieldSpec(name="code", data_type="string",
                  distribution={"kind": "string_pattern", "min_length": 16, "max_length": 24}),
        FieldSpec(name="untyped", data_type="string",
                  distribution={"kind": "string_pattern", "min_length": 12, "max_length": 12}),
        FieldSpec(name="email", data_type="string", sensitive=True, semantic_type="email"),
        FieldSpec(name="phone", data_type="string", sensitive=True, semantic_type="phone"),
    ]
    entities = [EntitySpec(name=name, row_count=17, primary_key="id",
                           fields=[field.model_copy(deep=True) for field in fields])
                for name in ("events", "other_events")]
    entities[1].field("quantity").distribution.update(min_value=101, max_value=140)
    return DatasetSpec(
        entities=entities,
        generation_settings={"mode": mode, "invalid_ratio": 0.35 if mode in {"mixed", "negative"} else 0.0, "locale": "en_US"},
    )


@pytest.mark.parametrize("mode", ["valid", "mixed", "negative"])
def test_parallel_counts_preserve_rows_csv_and_spec(mode):
    spec = diverse_spec(mode)
    original = spec.model_dump(mode="json")
    children = {process.pid for process in multiprocessing.active_children()}
    results = [generate_dataset_parallel(spec, seed=73, policy=ParallelGenerationPolicy(workers=count))
               for count in (1, 2, 4)]

    assert results[0] == results[1] == results[2]
    csv_outputs = [{name: rows_to_csv(rows) for name, rows in result.items()}
                   for result in results]
    assert csv_outputs[0] == csv_outputs[1] == csv_outputs[2]
    assert spec.model_dump(mode="json") == original
    assert {process.pid for process in multiprocessing.active_children()} <= children
    assert set(row["id"] for row in results[0]["events"]).isdisjoint(
        row["id"] for row in results[0]["other_events"])
    if mode == "valid":
        assert all(1 <= row["quantity"] <= 40 for row in results[0]["events"])
        assert all(101 <= row["quantity"] <= 140 for row in results[0]["other_events"])
        assert validate_dataset(results[0], spec).valid


def key_spec(rows):
    return DatasetSpec(entities=[EntitySpec(name="items", row_count=rows, primary_key="id", fields=[
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="group_id", data_type="string", is_identifier=True,
                  distribution={"kind": "synthetic_identifier", "pool_size": 4}),
        FieldSpec(name="code", data_type="string", nullable=True, null_ratio=0.25,
                  distribution={"kind": "string_pattern", "min_length": 16, "max_length": 24}),
    ])])


def test_parallel_tiles_preserve_order_tail_prefix_and_seed():
    spec = key_spec(TILE_ROWS + 7)
    results = [generate_dataset_parallel(spec, seed=29, policy=ParallelGenerationPolicy(workers=count))
               for count in (1, 2, 4)]
    assert results[0] == results[1] == results[2]
    rows = results[0]["items"]
    assert len(rows) == len({row["id"] for row in rows}) == TILE_ROWS + 7
    assert len({row["group_id"] for row in rows}) == 4
    assert [row["id"] for row in rows] == sorted(row["id"] for row in rows)
    prefix_spec = key_spec(TILE_ROWS + 2)
    replay = generate_dataset_parallel(prefix_spec, seed=29, policy=ParallelGenerationPolicy(workers=2))
    assert replay["items"] == rows[:TILE_ROWS + 2]
    other_seed = generate_dataset_parallel(key_spec(3), seed=30)
    assert other_seed["items"] != rows[:3]


def test_parallel_applies_cross_tile_relationships_formulas_and_aggregates():
    spec = DatasetSpec(
        entities=[
            EntitySpec(name="parents", row_count=3, primary_key="id", fields=[
                FieldSpec(name="id", data_type="integer", is_identifier=True),
                FieldSpec(name="total", data_type="integer"),
            ]),
            EntitySpec(name="children", row_count=TILE_ROWS + 3, primary_key="id", fields=[
                FieldSpec(name="id", data_type="integer", is_identifier=True),
                FieldSpec(name="parent_id", data_type="integer", is_identifier=True),
                FieldSpec(name="quantity", data_type="integer",
                          distribution={"kind": "numeric", "min_value": 1, "max_value": 5}),
                FieldSpec(name="twice", data_type="integer"),
            ]),
        ],
        relationships=[Relationship(parent_entity="parents", parent_field="id",
                                    child_entity="children", child_field="parent_id", confidence=1)],
        constraints=[
            Constraint(type="formula", entity="children", fields=["twice"],
                       expression="quantity * 2", confidence=1, status="confirmed"),
            Constraint(type="aggregate_mapping", entity="parents", fields=["total"],
                       target_entity="children", target_field="twice", aggregate="sum",
                       confidence=1, status="confirmed"),
        ],
    )
    single = generate_dataset_parallel(spec, seed=17, policy=ParallelGenerationPolicy(workers=1))
    parallel_rows = generate_dataset_parallel(spec, seed=17, policy=ParallelGenerationPolicy(workers=4))
    assert parallel_rows == single
    assert validate_dataset(parallel_rows, spec).valid
    for parent in parallel_rows["parents"]:
        assert parent["total"] == sum(row["twice"] for row in parallel_rows["children"]
                                      if row["parent_id"] == parent["id"])


@pytest.mark.parametrize("options", [
    {"workers": 0}, {"workers": 5}, {"workers": True},
    {"max_rows": 0}, {"max_rows": True}, {"max_cells": 0},
    {"engine": "unknown"}, {"unexpected": 1},
])
def test_parallel_policy_rejects_invalid_options(options):
    with pytest.raises(ValueError):
        ParallelGenerationPolicy(**options)


@pytest.mark.parametrize("seed", [-1, True, 1.5])
def test_parallel_rejects_invalid_seed_before_starting_processes(monkeypatch, seed):
    monkeypatch.setattr(parallel, "get_context", lambda *args: pytest.fail("unexpected process pool"))
    with pytest.raises(ValueError):
        generate_dataset_parallel(key_spec(3), seed=seed)


def test_parallel_limits_are_explicit_without_relaxing_legacy(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_COUNT", "2")
    spec = key_spec(3)
    with pytest.raises(ValueError, match="row"):
        generate_dataset_parallel(spec, seed=29)
    generated = generate_dataset_parallel(spec, seed=29, policy=ParallelGenerationPolicy(
        max_rows=3, max_cells=9,
    ))
    assert len(generated["items"]) == 3
    with pytest.raises(ValueError, match="row_count"):
        generate_dataset(spec, seed=29)


def test_parallel_rejects_cell_budget_before_starting_processes(monkeypatch):
    monkeypatch.setattr(parallel, "get_context", lambda *args: pytest.fail("unexpected process pool"))
    with pytest.raises(ValueError, match="cell"):
        generate_dataset_parallel(key_spec(3), seed=29,
                                  policy=ParallelGenerationPolicy(max_cells=8))


def test_parallel_rejects_empty_field_entities_before_starting_processes(monkeypatch):
    monkeypatch.setattr(parallel, "get_context", lambda *args: pytest.fail("unexpected process pool"))
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=3, fields=[])])
    with pytest.raises(ValueError, match="at least one field"):
        generate_dataset_parallel(spec, seed=29)


@pytest.fixture
def fake_pool(monkeypatch):
    pool = Mock()
    context = Mock()
    context.Pool.return_value = pool
    monkeypatch.setattr(parallel, "get_context", Mock(return_value=context))
    return pool


@pytest.mark.parametrize("stage", ["context", "startup", "submission", "terminate", "join"])
def test_parallel_orchestration_errors_are_redacted_and_attempt_cleanup(fake_pool, stage):
    spec = key_spec(1)
    fake_pool.apply_async.return_value.get.return_value = parallel._worker_tile(spec, 0, 0, 29, 1)
    canary = "synthetic_orchestration_canary"
    error = ValueError(canary)
    if stage == "context":
        parallel.get_context.side_effect = error
    elif stage == "startup":
        parallel.get_context.return_value.Pool.side_effect = error
    elif stage == "submission":
        fake_pool.apply_async.side_effect = error
    else:
        getattr(fake_pool, stage).side_effect = error
    handler = signal.getsignal(signal.SIGINT)
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, set()) if hasattr(signal, "pthread_sigmask") else None

    with pytest.raises(ParallelGenerationError) as raised:
        generate_dataset_parallel(spec, seed=29)

    assert canary not in str(raised.value)
    assert raised.value.__context__ is None
    assert signal.getsignal(signal.SIGINT) == handler
    if mask is not None:
        assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == mask
    if stage in {"context", "startup"}:
        fake_pool.terminate.assert_not_called()
        fake_pool.join.assert_not_called()
    else:
        fake_pool.terminate.assert_called_once_with()
        fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("failure", [
    KeyboardInterrupt(), SystemExit(21), GenerationLimitError("expected parent deadline"),
    ParallelGenerationError("expected worker failure"),
])
def test_parallel_preserves_primary_failure_when_cleanup_also_fails(monkeypatch, fake_pool, failure):
    monkeypatch.setattr(parallel, "_await_tile", Mock(side_effect=failure))
    fake_pool.terminate.side_effect = OSError("synthetic_cleanup_canary")
    fake_pool.join.side_effect = RuntimeError("synthetic_cleanup_canary")

    with pytest.raises(type(failure)) as raised:
        generate_dataset_parallel(key_spec(1), seed=29)

    assert raised.value is failure
    assert "synthetic_cleanup_canary" not in str(raised.value)
    assert raised.value.__context__ is None
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("stage", ["terminate", "join", "both"])
@pytest.mark.parametrize("interrupt_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("has_primary", [False, True])
def test_parallel_cleanup_interrupts_preserve_failure_and_attempt_join(
    monkeypatch, fake_pool, stage, interrupt_type, has_primary,
):
    spec = key_spec(1)
    interruption = interrupt_type("expected cleanup interrupt")
    primary = GenerationLimitError("expected parent deadline")
    if has_primary:
        monkeypatch.setattr(parallel, "_await_tile", Mock(side_effect=primary))
    else:
        fake_pool.apply_async.return_value.get.return_value = parallel._worker_tile(spec, 0, 0, 29, 1)
    if stage == "both":
        fake_pool.terminate.side_effect = interruption
        other_type = SystemExit if interrupt_type is KeyboardInterrupt else KeyboardInterrupt
        fake_pool.join.side_effect = other_type("secondary cleanup interrupt")
    else:
        getattr(fake_pool, stage).side_effect = interruption
    expected = primary if has_primary else interruption

    with pytest.raises(type(expected)) as raised:
        generate_dataset_parallel(spec, seed=29)

    assert raised.value is expected
    assert raised.value.__context__ is None
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("failure", [
    ValueError("synthetic_worker_canary"),
    parallel.TileOutcome(error="worker"),
    parallel.TileOutcome(),
    parallel.TileOutcome(rows=[]),
])
def test_parallel_failures_are_redacted_and_reap_workers(fake_pool, failure):
    result = fake_pool.apply_async.return_value
    if isinstance(failure, BaseException):
        result.get.side_effect = failure
    else:
        result.get.return_value = failure
    with pytest.raises(ParallelGenerationError) as raised:
        generate_dataset_parallel(key_spec(1), seed=29)
    assert "synthetic_worker_canary" not in str(raised.value)
    assert raised.value.__context__ is None
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


def test_parallel_keyboard_interrupt_reaps_workers(fake_pool):
    fake_pool.apply_async.return_value.get.side_effect = KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        generate_dataset_parallel(key_spec(1), seed=29)
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


def test_parallel_waiting_checks_parent_deadline_and_reaps_workers(fake_pool):
    now = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: now[0])

    def timeout(*args, **kwargs):
        now[0] = 2.0
        raise multiprocessing.TimeoutError

    fake_pool.apply_async.return_value.get.side_effect = timeout
    with pytest.raises(GenerationLimitError, match="budget"):
        generate_dataset_parallel(key_spec(1), seed=29, budget=budget)
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


def test_parallel_worker_limit_reaps_workers(fake_pool):
    fake_pool.apply_async.return_value.get.return_value = parallel.TileOutcome(error="limit")
    with pytest.raises(GenerationLimitError, match="resource budget"):
        generate_dataset_parallel(key_spec(1), seed=29)
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


def test_worker_cell_limit_is_not_reported_as_a_deadline(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "10")
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=1, fields=[
        FieldSpec(name="label", data_type="string", distribution={
            "kind": "string_pattern", "min_length": 11, "max_length": 11,
        }),
    ])])
    outcome = parallel._worker_tile(spec, 0, 0, 29, 60)
    assert outcome == parallel.TileOutcome(error="limit")
    result = Mock()
    result.get.return_value = outcome

    with pytest.raises(GenerationLimitError, match="resource budget") as caught:
        parallel._await_tile(result, GenerationBudget(60))

    assert "time" not in str(caught.value) and caught.value.__context__ is None


def test_parallel_limits_in_flight_tiles_and_preserves_order(fake_pool):
    outstanding = [0]
    high_water = [0]

    def submit(function, args):
        outstanding[0] += 1
        high_water[0] = max(high_water[0], outstanding[0])
        result = Mock()

        def receive(*args_, **kwargs):
            outstanding[0] -= 1
            return function(*args)

        result.get.side_effect = receive
        return result

    fake_pool.apply_async.side_effect = submit
    spec = key_spec(TILE_ROWS * 4 + 7)
    rows = generate_dataset_parallel(spec, seed=29,
                                     policy=ParallelGenerationPolicy(workers=2))["items"]
    assert high_water[0] == 2
    assert outstanding[0] == 0
    assert fake_pool.apply_async.call_count == 5
    assert len(rows) == len({row["id"] for row in rows}) == spec.entities[0].row_count
    assert [row["id"] for row in rows] == sorted(row["id"] for row in rows)
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


def test_tile_visitor_streams_ordered_batches_with_bounded_pending_work(fake_pool):
    outstanding = [0]
    high_water = [0]

    def submit(function, args):
        outstanding[0] += 1
        high_water[0] = max(high_water[0], outstanding[0])
        result = Mock()

        def receive(*args_, **kwargs):
            outstanding[0] -= 1
            return function(*args)

        result.get.side_effect = receive
        return result

    fake_pool.apply_async.side_effect = submit
    spec = key_spec(TILE_ROWS * 3 + 7)
    other = spec.entities[0].model_copy(deep=True)
    other.name = "other_items"
    other.row_count = 2
    spec.entities.append(other)
    visits = []

    def consume(entity_index, start, rows):
        assert outstanding[0] <= 1
        visits.append((entity_index, start, len(rows), rows[0]["id"]))
        spec.entities[0].row_count = 1

    parallel._visit_generated_tiles(
        spec, seed=29, policy=ParallelGenerationPolicy(workers=2),
        budget=GenerationBudget(), consume=consume,
    )

    assert [(entity, start, size) for entity, start, size, _ in visits] == [
        (0, 0, TILE_ROWS), (0, TILE_ROWS, TILE_ROWS),
        (0, TILE_ROWS * 2, TILE_ROWS), (0, TILE_ROWS * 3, 7), (1, 0, 2),
    ]
    first_keys = [key for entity, _, _, key in visits if entity == 0]
    assert first_keys == sorted(set(first_keys))
    assert high_water[0] == 2
    assert outstanding[0] == 0
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("error_type", [ValueError, ParallelGenerationError, GenerationLimitError])
def test_tile_visitor_redacts_consumer_failures_and_reaps_workers(fake_pool, error_type):
    spec = key_spec(1)
    fake_pool.apply_async.return_value.get.return_value = parallel._worker_tile(spec, 0, 0, 29, 1)
    consume = Mock(side_effect=error_type("synthetic_consumer_canary"))

    with pytest.raises(ParallelGenerationError, match="consumer failed") as raised:
        parallel._visit_generated_tiles(
            spec, seed=29, policy=ParallelGenerationPolicy(),
            budget=GenerationBudget(), consume=consume,
        )

    assert "synthetic_consumer_canary" not in str(raised.value)
    assert raised.value.__context__ is None
    consume.assert_called_once()
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("failure", [KeyboardInterrupt(), SystemExit(21)])
def test_tile_visitor_preserves_consumer_cancellation_and_reaps_workers(fake_pool, failure):
    spec = key_spec(1)
    fake_pool.apply_async.return_value.get.return_value = parallel._worker_tile(spec, 0, 0, 29, 1)

    with pytest.raises(type(failure)) as raised:
        parallel._visit_generated_tiles(
            spec, seed=29, policy=ParallelGenerationPolicy(),
            budget=GenerationBudget(), consume=Mock(side_effect=failure),
        )

    assert raised.value is failure
    assert raised.value.__context__ is None
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("violation", ["schema", "privacy"])
def test_parallel_always_validates_worker_rows_before_return(fake_pool, violation):
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=1, fields=[
        FieldSpec(name="email", data_type="string", sensitive=True, semantic_type="email"),
    ])])
    for setting in ("validate_schema", "validate_privacy", "validate_relationships", "validate_constraints"):
        setattr(spec.validation_settings, setting, False)
    value = 12345 if violation == "schema" else "synthetic_canary@fictional.invalid"
    fake_pool.apply_async.return_value.get.return_value = parallel.TileOutcome(rows=[{"email": value}])
    with pytest.raises(GenerationValidationError):
        generate_dataset_parallel(spec, seed=29)
    fake_pool.terminate.assert_called_once_with()
    fake_pool.join.assert_called_once_with()


@pytest.mark.parametrize("failure,error", [
    (ValueError("synthetic_worker_canary"), "worker"),
    (KeyboardInterrupt(), "worker"),
    (SystemExit(), "worker"),
    (GenerationLimitError("synthetic_worker_canary"), "limit"),
])
def test_worker_returns_only_error_code(monkeypatch, failure, error):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(parallel, "generate_tile", fail)
    outcome = parallel._worker_tile(key_spec(1), 0, 0, 29, 1)
    assert outcome == parallel.TileOutcome(error=error)
    assert "synthetic_worker_canary" not in repr(outcome)
