"""Public CSV streaming retains complete validation and atomic file behavior."""

from __future__ import annotations

import builtins
from contextlib import contextmanager
import traceback

import pytest

from test_data_agent.adapters.parallel_generation import (
    ParallelGenerationPolicy,
    generate_dataset_parallel,
)
from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.relationship import Relationship
from test_data_agent.io import streaming_csv as streaming
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation import validate_dataset
from test_data_agent.validation.reconciliation import GenerationValidationError


CANARY = "synthetic_streaming_failure@fictional.invalid"


def spec_for(rows=2, *, primary_key="id") -> DatasetSpec:
    return DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=rows, primary_key=primary_key,
        fields=[
            FieldSpec(name="id", data_type="integer", is_identifier=True),
            FieldSpec(name="amount", data_type="float", nullable=True),
            FieldSpec(name="active", data_type="boolean", nullable=True),
            FieldSpec(name="day", data_type="date", nullable=True),
            FieldSpec(name="instant", data_type="datetime", nullable=True),
            FieldSpec(name="label", data_type="string", nullable=True),
        ],
    )])


def records():
    return [
        {"id": 1, "amount": 1, "active": True, "day": "2024-02-29",
         "instant": "2024-02-29T00:00:00+03:00", "label": "synthetic_кириллица,\"quoted\"\nline"},
        {"id": 2, "amount": "01.50", "active": "false", "day": None,
         "instant": None, "label": " =synthetic_formula"},
    ]


@pytest.fixture
def fake_tiles(monkeypatch):
    def install(rows=None, *, step=1):
        rows = records() if rows is None else rows

        def visit(spec, seed, *, policy, budget, consume):
            for start in range(0, len(rows), step):
                consume(0, start, rows[start:start + step])

        monkeypatch.setattr(streaming, "_visit_generated_tiles", visit)

    install()
    return install


def write(spec, folder, *, workers=1, budget=None, policy=None):
    return streaming.write_streaming_csv(
        spec, output_folder=folder, seed=42,
        policy=policy or ParallelGenerationPolicy(workers=workers),
        budget=budget or GenerationBudget(60),
    )


def assert_unpublished(folder):
    assert not (folder / "fictional.csv").exists()
    assert not list(folder.glob("*.tmp"))


def test_scalar_csv_and_report_match_full_validation(tmp_path, fake_tiles):
    spec = spec_for()
    original = spec.model_dump(mode="json")

    report = write(spec, tmp_path)

    assert (tmp_path / "fictional.csv").read_bytes() == rows_to_csv(records(), typed=True).encode()
    assert report == validate_dataset({"fictional": records()}, spec)
    assert all(section.failed == 0 for section in report.sections)
    assert spec.model_dump(mode="json") == original
    assert (tmp_path / "fictional.csv").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("workers", (1, 2, 4))
def test_real_spawn_matches_complete_tiled_generation_at_partial_last_tile(tmp_path, workers):
    spec = spec_for(4101)
    reference = generate_dataset_parallel(spec, 42, policy=ParallelGenerationPolicy(workers=1))

    report = write(spec, tmp_path, workers=workers)

    assert (tmp_path / "fictional.csv").read_bytes() == rows_to_csv(reference["fictional"]).encode()
    assert report == validate_dataset(reference, spec)


def test_primary_key_is_optional(tmp_path, fake_tiles):
    spec = spec_for(primary_key=None)
    rows = records()
    rows[1]["id"] = rows[0]["id"]
    fake_tiles(rows)

    assert write(spec, tmp_path).valid
    assert (tmp_path / "fictional.csv").read_bytes() == rows_to_csv(rows, typed=True).encode()


@pytest.mark.parametrize("keys", ((1, 1), (1, "1"), (" 1", "1")))
def test_global_primary_key_uniqueness_includes_normalized_values(tmp_path, fake_tiles, keys):
    rows = records()
    for row, key in zip(rows, keys, strict=True):
        row["id"] = key
    fake_tiles(rows)

    with pytest.raises(GenerationValidationError, match="primary keys"):
        write(spec_for(), tmp_path)

    assert_unpublished(tmp_path)


@pytest.mark.parametrize("violation", ("privacy", "type", "shape", "null"))
def test_mandatory_validation_precedes_csv_encoding_with_report_flags_disabled(
    tmp_path, fake_tiles, monkeypatch, violation,
):
    rows = records()
    if violation == "privacy":
        rows[0]["label"] = CANARY
    elif violation == "type":
        rows[0]["id"] = "synthetic_not_integer"
    elif violation == "shape":
        del rows[0]["label"]
    else:
        rows[0]["id"] = None
    fake_tiles(rows)
    spec = spec_for()
    for setting in ("validate_schema", "validate_relationships", "validate_constraints", "validate_privacy"):
        setattr(spec.validation_settings, setting, False)
    monkeypatch.setattr(streaming.csv, "writer", lambda *args, **kwargs: pytest.fail("invalid rows encoded"))

    with pytest.raises(GenerationValidationError) as caught:
        write(spec, tmp_path)

    assert CANARY not in str(caught.value)
    assert_unpublished(tmp_path)


def test_disabled_report_sections_remain_disabled(tmp_path, fake_tiles):
    spec = spec_for()
    spec.validation_settings.validate_schema = False
    spec.validation_settings.validate_relationships = False
    spec.validation_settings.validate_constraints = False
    spec.validation_settings.validate_privacy = False

    report = write(spec, tmp_path)

    assert report == validate_dataset({"fictional": records()}, spec)
    assert report.valid and report.sections == []


def test_report_validation_failure_prevents_publication(tmp_path, fake_tiles, monkeypatch):
    report = validate_dataset({"fictional": records()}, spec_for())
    report.valid = False
    report.sections[0].failed = 1
    report.sections[0].errors = [CANARY]
    monkeypatch.setattr(streaming, "_validate_generated_dataset", lambda data, spec, **kwargs: (report, data))

    with pytest.raises(GenerationValidationError) as caught:
        write(spec_for(), tmp_path)

    assert CANARY not in str(caught.value)
    assert_unpublished(tmp_path)


def test_cumulative_byte_limit_preserves_existing_output(tmp_path, fake_tiles, monkeypatch):
    existing = tmp_path / "fictional.csv"
    existing.write_bytes(b"synthetic_previous\r\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", str(len(rows_to_csv(records(), typed=True).encode()) - 1))

    with pytest.raises(GenerationLimitError, match="bytes"):
        write(spec_for(), tmp_path)

    assert existing.read_bytes() == b"synthetic_previous\r\n"
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("kind", ("relationship", "constraint", "mode", "entities", "fields"))
def test_unsupported_specification_fails_before_opening_output(tmp_path, monkeypatch, kind):
    spec = spec_for()
    if kind == "relationship":
        spec.relationships = [Relationship(parent_entity="fictional", parent_field="id",
                                            child_entity="fictional", child_field="id", confidence=1)]
    elif kind == "constraint":
        spec.constraints = [Constraint(type="formula", entity="fictional", fields=["amount"],
                                       expression="id * 2", confidence=1)]
    elif kind == "mode":
        spec.generation_settings.mode = "negative"
    elif kind == "entities":
        spec.entities = []
    else:
        spec.entities = [EntitySpec(name="fictional", row_count=2)]
    monkeypatch.setattr(streaming, "_visit_generated_tiles", lambda *args, **kwargs: pytest.fail("workers started"))
    monkeypatch.setattr(streaming, "atomic_binary_writer", lambda *args: pytest.fail("output opened"))

    assert not streaming.can_stream_csv(spec)
    with pytest.raises(streaming.StreamingCsvError, match="does not support"):
        write(spec, tmp_path)


@pytest.mark.parametrize("policy", (ParallelGenerationPolicy(max_rows=1), ParallelGenerationPolicy(max_cells=1)))
def test_policy_limits_fail_before_output(tmp_path, monkeypatch, policy):
    monkeypatch.setattr(streaming, "atomic_binary_writer", lambda *args: pytest.fail("output opened"))

    with pytest.raises((ValueError, GenerationLimitError)):
        write(spec_for(), tmp_path, policy=policy)


def test_oversized_tile_fails_before_output_or_workers(tmp_path, monkeypatch):
    spec = DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=streaming.TILE_ROWS,
        fields=[FieldSpec(name="label", data_type="string", distribution={
            "kind": "string_pattern", "min_length": 1_000_000, "max_length": 1_000_000,
        })],
    )])
    monkeypatch.setattr(streaming, "atomic_binary_writer", lambda *a, **kw: pytest.fail("output opened"))
    monkeypatch.setattr(streaming, "_visit_generated_tiles", lambda *a, **kw: pytest.fail("workers started"))

    with pytest.raises(GenerationLimitError, match="estimated streaming CSV in-flight data"):
        write(spec, tmp_path)

    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("workers", (1, 2, 4))
def test_in_flight_allocation_admission_accounts_for_workers(tmp_path, monkeypatch, workers):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", str(12 * 1024 * 1024))
    spec = DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=streaming.TILE_ROWS * 4,
        fields=[FieldSpec(name="label", data_type="string", distribution={
            "kind": "string_pattern", "min_length": 1000, "max_length": 1000,
        })],
    )])

    def stop_before_generation(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(streaming, "_visit_generated_tiles", stop_before_generation)
    if workers == 1:
        with pytest.raises(KeyboardInterrupt):
            write(spec, tmp_path, workers=workers)
    else:
        monkeypatch.setattr(streaming, "atomic_binary_writer", lambda *a, **kw: pytest.fail("output opened"))
        with pytest.raises(GenerationLimitError, match="estimated streaming CSV in-flight data"):
            write(spec, tmp_path, workers=workers)
    assert_unpublished(tmp_path)


@pytest.mark.parametrize("workers", (1, 2, 4))
def test_large_narrow_csv_passes_bounded_allocation_admission(tmp_path, monkeypatch, workers):
    spec = DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=750_000,
        fields=[FieldSpec(name=f"metric_{index}", data_type="integer") for index in range(25)],
    )])

    def stop_before_generation(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(streaming, "_visit_generated_tiles", stop_before_generation)
    with pytest.raises(KeyboardInterrupt):
        write(spec, tmp_path, policy=ParallelGenerationPolicy(
            workers=workers, max_rows=1_000_000, max_cells=25_000_000,
        ))
    assert spec.entities[0].row_count == 750_000
    assert_unpublished(tmp_path)


@pytest.mark.parametrize("kind", ("count", "start", "entity", "empty"))
def test_sequence_and_final_count_are_checked(tmp_path, monkeypatch, kind):
    def visit(spec, seed, *, policy, budget, consume):
        consume(1 if kind == "entity" else 0, 1 if kind == "start" else 0,
                [] if kind == "empty" else records()[:1])

    monkeypatch.setattr(streaming, "_visit_generated_tiles", visit)

    with pytest.raises(GenerationValidationError):
        write(spec_for(), tmp_path)

    assert_unpublished(tmp_path)


@pytest.mark.parametrize("kind", ("write", "close"))
def test_native_io_failure_is_value_free_and_unpublished(tmp_path, fake_tiles, monkeypatch, kind):
    original = streaming.atomic_binary_writer

    @contextmanager
    def broken(path):
        with original(path) as handle:
            if kind == "write":
                class BrokenHandle:
                    def write(self, payload):
                        raise OSError(CANARY)
                yield BrokenHandle()
            else:
                yield handle
                raise OSError(CANARY)

    monkeypatch.setattr(streaming, "atomic_binary_writer", broken)

    with pytest.raises(streaming.StreamingCsvError) as caught:
        write(spec_for(), tmp_path)

    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_unpublished(tmp_path)


@pytest.mark.parametrize("cancellation", (KeyboardInterrupt, SystemExit))
def test_cancellation_keeps_identity_and_removes_temporary_output(tmp_path, monkeypatch, cancellation):
    error = cancellation()

    def cancel(*args, **kwargs):
        raise error

    monkeypatch.setattr(streaming, "_visit_generated_tiles", cancel)

    with pytest.raises(cancellation) as caught:
        write(spec_for(), tmp_path)

    assert caught.value is error
    assert_unpublished(tmp_path)


def test_expired_budget_is_preserved_before_output(tmp_path):
    now = [0.0]
    budget = GenerationBudget(1, clock=lambda: now[0])
    now[0] = 2

    with pytest.raises(GenerationLimitError, match="budget"):
        write(spec_for(), tmp_path, budget=budget)

    assert_unpublished(tmp_path)


def test_streaming_csv_has_no_arrow_or_duckdb_dependency(tmp_path, fake_tiles, monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"pyarrow", "duckdb"}:
            pytest.fail("CSV streaming imported an optional backend")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    assert write(spec_for(), tmp_path).valid
