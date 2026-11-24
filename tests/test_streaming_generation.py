"""Experimental streaming sinks retain seeded output and fail before publication."""

from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import traceback
from types import SimpleNamespace

import pytest

from scripts import benchmark_parallel_generation as benchmark
from scripts import streaming_generation as streaming
from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy
from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation.tiled_generator import TILE_ROWS, generate_tile
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation.reconciliation import GenerationValidationError


CANARY = "synthetic_streaming_canary@fictional.invalid"


@pytest.fixture(autouse=True)
def script_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    pytest.importorskip("pyarrow")


@pytest.fixture(params=("arrow", "duckdb"))
def backend(request: pytest.FixtureRequest) -> str:
    if request.param == "duckdb":
        pytest.importorskip("duckdb")
    return request.param


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    path = tmp_path.resolve() / "private"
    path.mkdir(mode=0o700)
    return path


@pytest.fixture
def fake_tiles(monkeypatch: pytest.MonkeyPatch):
    def install(*, mutate=None, split_size=None, on_consume=None):
        def visit(spec, seed, *, policy, budget, consume):
            for entity_index, entity in enumerate(spec.entities):
                for start in range(0, entity.row_count, TILE_ROWS):
                    rows = generate_tile(spec, entity_index, start, seed, budget=budget)
                    if mutate is not None:
                        mutate(rows, start)
                    step = split_size or len(rows)
                    for offset in range(0, len(rows), step):
                        if on_consume is not None:
                            on_consume()
                        consume(entity_index, start + offset, rows[offset:offset + step])

        monkeypatch.setattr(streaming, "_visit_generated_tiles", visit)

    install()
    return install


def stream(spec: DatasetSpec, backend: str, scratch: Path, *, budget=None):
    entity = spec.entities[0]
    return streaming._stream(
        spec, backend, seed=42, scratch=scratch,
        policy=ParallelGenerationPolicy(workers=4, max_rows=entity.row_count,
                                        max_cells=entity.row_count * len(entity.fields)),
        budget=budget or GenerationBudget(60),
    )


def assert_unpublished(scratch: Path) -> None:
    assert not (scratch / "synthetic.csv").exists()
    assert not list(scratch.rglob("*.tmp"))


def test_streaming_csv_matches_full_reference_across_tile_boundary(
    backend: str, scratch: Path, fake_tiles,
) -> None:
    spec = benchmark.fictional_spec(TILE_ROWS + 5)
    rows = [row for start in range(0, spec.entities[0].row_count, TILE_ROWS)
            for row in generate_tile(spec, 0, start, 42, budget=GenerationBudget(60))]
    reference = rows_to_csv(rows).encode()

    result = stream(spec, backend, scratch)

    assert (scratch / "synthetic.csv").read_bytes() == reference
    assert result["csv_bytes"] == len(reference)
    assert result["csv_sha256"] == hashlib.sha256(reference).hexdigest()
    assert result["rows_validated"] == TILE_ROWS + 5
    assert result["unique_primary_keys"]
    assert result["scratch_private"] and result["output_private"]
    assert stat.S_IMODE(scratch.stat().st_mode) == 0o700
    assert stat.S_IMODE((scratch / "synthetic.csv").stat().st_mode) == 0o600
    assert all(value >= 0 for value in result["stage_seconds"].values())


def test_cross_batch_duplicate_primary_key_prevents_publication(
    backend: str, scratch: Path, fake_tiles,
) -> None:
    def duplicate(rows, start):
        rows[1]["row_id"] = rows[0]["row_id"]

    fake_tiles(mutate=duplicate, split_size=1)

    with pytest.raises(streaming.StreamingBenchmarkError, match="primary key"):
        stream(benchmark.fictional_spec(2), backend, scratch)

    assert_unpublished(scratch)


@pytest.mark.parametrize("violation", ("privacy", "type", "missing", "null"))
def test_mandatory_validation_precedes_arrow_conversion_and_output(
    backend: str, scratch: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch,
    violation: str,
) -> None:
    import pyarrow as pa

    def corrupt(rows, start):
        if violation == "privacy":
            rows[0]["value_4"] = CANARY
        elif violation == "type":
            rows[0]["value_0"] = "synthetic_not_an_integer"
        elif violation == "missing":
            del rows[0]["value_5"]
        else:
            rows[0]["value_0"] = None

    original_array = pa.array

    def reject_nonempty_array(values, *args, **kwargs):
        assert not len(values), "invalid candidates reached Arrow conversion"
        return original_array(values, *args, **kwargs)

    monkeypatch.setattr(pa, "array", reject_nonempty_array)
    fake_tiles(mutate=corrupt)
    spec = benchmark.fictional_spec(2)
    for setting in ("validate_schema", "validate_privacy", "validate_relationships",
                    "validate_constraints"):
        setattr(spec.validation_settings, setting, False)

    with pytest.raises(GenerationValidationError) as caught:
        stream(spec, backend, scratch)

    assert CANARY not in str(caught.value)
    assert_unpublished(scratch)
    assert all(path.stat().st_size == 0 for path in scratch.rglob("*") if path.is_file())


def test_arrow_round_trip_keeps_csv_scalar_values_and_formula_neutralization(
    backend: str, scratch: Path, fake_tiles,
) -> None:
    text_field = " =synthetic_header"
    values = [
        (True, 0.1, "2024-02-29", "synthetic_кириллица,\"quoted\"\nline"),
        (False, -0.0, "2020-01-01", " =synthetic_formula"),
        (None, 1e-20, None, "\tsynthetic_tab"),
        (True, None, "2025-01-01", "@synthetic_formula"),
        (False, 1e20, "2021-12-31", None),
    ]
    spec = DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=len(values), primary_key="row_id", fields=[
            FieldSpec(name="row_id", data_type="integer", is_identifier=True),
            FieldSpec(name="active", data_type="boolean", nullable=True),
            FieldSpec(name="amount", data_type="float", nullable=True),
            FieldSpec(name="day", data_type="date", nullable=True),
            FieldSpec(name=text_field, data_type="string", nullable=True),
        ],
    )])

    def replace(rows, start):
        for row, (active, amount, day, text) in zip(rows, values, strict=True):
            row.update(active=active, amount=amount, day=day)
            row[text_field] = text

    fake_tiles(mutate=replace, split_size=2)
    reference_rows = generate_tile(spec, 0, 0, 42, budget=GenerationBudget(60))
    replace(reference_rows, 0)

    stream(spec, backend, scratch)

    assert (scratch / "synthetic.csv").read_bytes() == rows_to_csv(reference_rows).encode()


def test_output_limit_prevents_atomic_publication(
    backend: str, scratch: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "1")

    with pytest.raises(GenerationLimitError, match="bytes"):
        stream(benchmark.fictional_spec(2), backend, scratch)

    assert_unpublished(scratch)


def test_failed_output_preserves_existing_file(
    backend: str, scratch: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = b"synthetic_existing_output\r\n"
    output = scratch / "synthetic.csv"
    output.write_bytes(previous)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "1")

    with pytest.raises(GenerationLimitError):
        stream(benchmark.fictional_spec(2), backend, scratch)

    assert output.read_bytes() == previous
    assert not list(scratch.rglob("*.tmp"))


@pytest.mark.parametrize("violation", ("count", "start", "entity"))
def test_invalid_tile_sequence_or_total_prevents_publication(
    backend: str, scratch: Path, monkeypatch: pytest.MonkeyPatch, violation: str,
) -> None:
    def visit(spec, seed, *, policy, budget, consume):
        rows = generate_tile(spec, 0, 0, seed, budget=budget)
        consume(1 if violation == "entity" else 0, 1 if violation == "start" else 0,
                rows[:1] if violation == "count" else rows)

    monkeypatch.setattr(streaming, "_visit_generated_tiles", visit)

    with pytest.raises(streaming.StreamingBenchmarkError):
        stream(benchmark.fictional_spec(2), backend, scratch)

    assert_unpublished(scratch)


@pytest.mark.parametrize("unsupported", ("constraint", "relationship", "mode", "entities", "key"))
def test_unsupported_specifications_fail_before_generation_or_duckdb(
    scratch: Path, monkeypatch: pytest.MonkeyPatch, unsupported: str,
) -> None:
    spec = benchmark.fictional_spec(2)
    if unsupported == "constraint":
        spec.constraints = [Constraint(
            type="formula", entity="fictional", fields=["value_6"],
            expression="value_0 * 2", confidence=1, status="confirmed",
        )]
    elif unsupported == "relationship":
        spec.relationships = [Relationship(
            parent_entity="fictional", parent_field="row_id", child_entity="fictional",
            child_field="value_0", confidence=1,
        )]
    elif unsupported == "mode":
        spec.generation_settings.mode = "mixed"
    elif unsupported == "entities":
        other = spec.entities[0].model_copy(deep=True)
        other.name = "other_fictional"
        spec.entities.append(other)
    else:
        spec.entities[0].primary_key = None
    monkeypatch.setattr(streaming, "_visit_generated_tiles",
                        lambda *args, **kwargs: pytest.fail("unsupported generation started"))
    duckdb = pytest.importorskip("duckdb")
    monkeypatch.setattr(duckdb, "connect",
                        lambda *args, **kwargs: pytest.fail("unsupported DuckDB connection opened"))

    with pytest.raises(streaming.StreamingBenchmarkError, match="flat valid"):
        stream(spec, "duckdb", scratch)

    assert list(scratch.iterdir()) == []


@pytest.fixture
def observed_duckdb(monkeypatch: pytest.MonkeyPatch):
    duckdb = pytest.importorskip("duckdb")
    original_connect = duckdb.connect
    state = SimpleNamespace(records=[], fail_at=None)

    class ObservedConnection:
        def __init__(self, connection, config):
            self.connection = connection
            self.config = config
            self.scratch = Path(config["temp_directory"]).parent
            self.queries = []
            self.closed = False
            state.records.append(self)
            assert stat.S_IMODE(self.scratch.stat().st_mode) == 0o700

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def execute(self, sql, *args, **kwargs):
            self.queries.append((sql, args))
            if ((state.fail_at == "insert" and sql.startswith("INSERT"))
                    or (state.fail_at == "global" and "count(DISTINCT" in sql)):
                raise duckdb.Error(CANARY)
            return self.connection.execute(sql, *args, **kwargs)

        def register(self, name, batch):
            if batch.num_rows and state.fail_at == "register":
                raise duckdb.Error(CANARY)
            return self.connection.register(name, batch)

        def sql(self, query):
            if state.fail_at == "readback":
                raise duckdb.Error(CANARY)
            return self.connection.sql(query)

        def close(self):
            assert self.scratch.exists(), "scratch must outlive the native connection"
            self.connection.close()
            self.closed = True
            if state.fail_at == "close":
                raise OSError(CANARY)

    def connect(database, *, config):
        assert database == ":memory:"
        return ObservedConnection(original_connect(database, config=config), config)

    monkeypatch.setattr(duckdb, "connect", connect)
    return state


def test_duckdb_configuration_is_private_bounded_and_disables_external_access(
    scratch: Path, fake_tiles, observed_duckdb,
) -> None:
    stream(benchmark.fictional_spec(3), "duckdb", scratch)

    record, = observed_duckdb.records
    assert record.closed
    assert record.config["memory_limit"] == "128MiB"
    assert record.config["threads"] == record.config["async_threads"] == "1"
    for setting in ("enable_external_access", "autoinstall_known_extensions",
                    "autoload_known_extensions", "python_enable_replacements"):
        assert record.config[setting] == "false"
    assert Path(record.config["temp_directory"]).parent == scratch
    queries = [sql for sql, _ in record.queries]
    assert "SET enable_logging = false" in queries
    assert "SET max_temp_directory_size = '2GiB'" in queries
    assert any(sql == "SET max_execution_time = ?" and args[0][0] > 0
               for sql, args in record.queries)
    assert not any(sql.startswith(("COPY", "INSTALL", "LOAD")) for sql in queries)


def test_run_wrapper_removes_private_scratch_after_success(
    backend: str, tmp_path: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(streaming.tempfile, "tempdir", str(tmp_path.resolve()))

    result = streaming.run_streaming_benchmark(3, backend)

    assert result["scratch_private"] and result["output_private"] and result["scratch_removed"]
    assert result["coordinator_peak_rss_bytes"] > 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("stage", ("register", "insert", "global", "readback", "close"))
def test_native_failures_are_redacted_and_scratch_is_removed(
    tmp_path: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch, observed_duckdb,
    capsys: pytest.CaptureFixture[str], stage: str,
) -> None:
    monkeypatch.setattr(streaming.tempfile, "tempdir", str(tmp_path.resolve()))
    observed_duckdb.fail_at = stage

    with pytest.raises(streaming.StreamingBenchmarkError) as caught:
        streaming.run_streaming_benchmark(2, "duckdb")

    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert CANARY not in str(capsys.readouterr())
    assert all(record.closed for record in observed_duckdb.records)
    assert list(tmp_path.iterdir()) == []


def test_deadline_failure_preserves_budget_error_and_removes_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [0.0]
    original_budget = GenerationBudget
    monkeypatch.setattr(streaming.tempfile, "tempdir", str(tmp_path.resolve()))
    monkeypatch.setattr(streaming, "GenerationBudget",
                        lambda seconds: original_budget(1, clock=lambda: now[0]))

    def expire(spec, seed, *, policy, budget, consume):
        now[0] = 2
        budget.check("synthetic test deadline")

    monkeypatch.setattr(streaming, "_visit_generated_tiles", expire)

    with pytest.raises(GenerationLimitError, match="budget") as caught:
        streaming.run_streaming_benchmark(2, "arrow")

    assert caught.value.__context__ is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("cancellation", (KeyboardInterrupt, SystemExit))
def test_cancellation_removes_private_scratch(
    backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cancellation,
) -> None:
    monkeypatch.setattr(streaming.tempfile, "tempdir", str(tmp_path.resolve()))
    interruption = cancellation()

    def cancel(*args, **kwargs):
        raise interruption

    monkeypatch.setattr(streaming, "_visit_generated_tiles", cancel)

    with pytest.raises(cancellation) as caught:
        streaming.run_streaming_benchmark(2, backend)

    assert caught.value is interruption
    assert list(tmp_path.iterdir()) == []


def test_scratch_cleanup_failure_is_redacted_and_prevents_success(
    tmp_path: Path, fake_tiles, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_directory = streaming.tempfile.TemporaryDirectory

    class FailedCleanup(original_directory):
        def cleanup(self):
            super().cleanup()
            raise OSError(CANARY)

    monkeypatch.setattr(streaming.tempfile, "tempdir", str(tmp_path.resolve()))
    monkeypatch.setattr(streaming.tempfile, "TemporaryDirectory", FailedCleanup)

    with pytest.raises(streaming.StreamingBenchmarkError) as caught:
        streaming.run_streaming_benchmark(2, "arrow")

    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert list(tmp_path.iterdir()) == []
