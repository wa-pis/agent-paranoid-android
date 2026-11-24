from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import tempfile
import traceback
from types import SimpleNamespace

import pytest

from test_data_agent.core.limits import InputLimitError
from test_data_agent.profiling import (
    LocalProfileBudget,
    LocalProfileDimension,
    LocalProfileLimitError,
    LocalProfileLimits,
    profile_example_folder,
)


CANARY = "fictional-private-marker-for-distinct-tests"


def digest(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


@pytest.fixture
def engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    duckdb = pytest.importorskip("duckdb")
    pa = pytest.importorskip("pyarrow")
    from test_data_agent.profiling import duckdb_distinct

    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir(mode=0o700)
    monkeypatch.setattr(tempfile, "tempdir", str(scratch_parent))
    original_connect = duckdb.connect
    state = SimpleNamespace(
        module=duckdb_distinct, duckdb=duckdb, pa=pa, scratch=scratch_parent,
        records=[], on_query=None, on_register=None,
    )

    class ObservedConnection:
        def __init__(self, connection, config):
            self.connection = connection
            self.config = config
            self.path = Path(config["temp_directory"])
            self.queries = []
            self.reader = None
            self.closed = False
            state.records.append(self)
            assert self.path.parent == scratch_parent
            assert stat.S_IMODE(self.path.stat().st_mode) == 0o700

        def execute(self, query, *args, **kwargs):
            self.queries.append((query, args))
            if query.startswith("SELECT") and state.on_query is not None:
                state.on_query(self)
            return self.connection.execute(query, *args, **kwargs)

        def register(self, name, reader):
            self.reader = reader
            if state.on_register is not None:
                reader = state.on_register(self, reader)
            return self.connection.register(name, reader)

        def close(self):
            assert self.path.exists(), "scratch must outlive the connection"
            self.connection.close()
            self.closed = True

    def connect(database, *, config):
        assert database == ":memory:"
        return ObservedConnection(original_connect(database, config=config), config)

    monkeypatch.setattr(duckdb, "connect", connect)
    return state


def assert_clean(engine) -> None:
    assert engine.records
    assert all(record.closed for record in engine.records)
    assert list(engine.scratch.iterdir()) == []


def test_arrow_receives_only_ordinals_and_fresh_keyed_digests(
    engine, monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = engine.module
    monkeypatch.setattr(module, "BATCH_DIGESTS", 2)
    original_hmac = module.hmac.digest
    keys = []
    captured = []

    def keyed(key, value, algorithm):
        if key not in keys:
            keys.append(key)
        return original_hmac(key, value, algorithm)

    def inspect_reader(record, reader):
        tokens = []
        captured.append(tokens)

        def batches():
            for batch in reader:
                assert batch.num_rows <= 2
                assert batch.schema.names == ["column_id", "digest"]
                assert batch.schema.types == [engine.pa.int32(), engine.pa.binary(32)]
                tokens.extend(zip(batch.column(0).to_pylist(), batch.column(1).to_pylist()))
                yield batch

        return engine.pa.RecordBatchReader.from_batches(reader.schema, batches())

    monkeypatch.setattr(module.hmac, "digest", keyed)
    engine.on_register = inspect_reader
    first, second = digest(CANARY), digest("fictional-other-value")
    for _ in range(2):
        initial = [{first}, set()]
        counts = module.count_distinct_stream(
            initial, iter([(0, first), (0, second), (1, first)]), LocalProfileBudget(),
        )
        assert counts == [2, 1]
        assert initial == [set(), set()]

    assert len(keys) == 2 and all(len(key) == 32 for key in keys)
    assert captured[0] != captured[1]
    for key, tokens in zip(keys, captured, strict=True):
        expected_first = original_hmac(key, first, "sha256")
        expected_second = original_hmac(key, second, "sha256")
        assert tokens == [(0, expected_first), (0, expected_first),
                          (0, expected_second), (1, expected_first)]
        assert all(token not in {first, second, key} for _, token in tokens)
    for record in engine.records:
        assert record.config["threads"] == record.config["async_threads"] == "1"
        for setting in ("enable_external_access", "autoinstall_known_extensions",
                        "autoload_known_extensions", "python_enable_replacements"):
            assert record.config[setting] == "false"
        query_names = [query for query, _ in record.queries]
        assert "SET enable_logging = false" in query_names
        assert query_names.index("SET lock_configuration = true") < len(query_names) - 1
        assert any(query == "SET max_execution_time = ?" and args[0][0] > 0
                   for query, args in record.queries)
    assert_clean(engine)


def test_native_failure_is_value_free_and_leaves_no_partial_cache(
    engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys,
) -> None:
    from test_data_agent.profiling import schema_profiler

    def fail_query(record):
        raise engine.duckdb.Error(CANARY)

    engine.on_query = fail_query
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 0)
    source, cache = tmp_path / "source", tmp_path / "cache"
    source.mkdir()
    (source / "items.csv").write_text("id\n1\n2\n", encoding="utf-8")
    with pytest.raises(engine.module.DistinctTrackingError) as caught:
        profile_example_folder(source, cache_dir=cache)

    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert CANARY not in str(capsys.readouterr())
    assert not cache.exists() or not list(cache.glob("*.json"))
    assert_clean(engine)


@pytest.mark.parametrize("cancellation", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("stage", ["query", "producer"])
def test_cancellation_closes_connection_and_removes_scratch(engine, cancellation, stage) -> None:
    def cancel(record):
        raise cancellation()

    def remaining():
        raise cancellation()
        yield

    if stage == "query":
        engine.on_query = cancel
    with pytest.raises(cancellation):
        engine.module.count_distinct_stream(
            [{digest(CANARY)}], remaining() if stage == "producer" else iter(()),
            LocalProfileBudget(),
        )
    assert_clean(engine)


def test_wrapped_producer_budget_error_preserves_its_dimension(engine) -> None:
    budget = LocalProfileBudget(LocalProfileLimits(max_input_cells=1))

    def remaining():
        yield 0, digest(CANARY)
        budget.consume_cells(2)

    with pytest.raises(LocalProfileLimitError) as caught:
        engine.module.count_distinct_stream([set()], remaining(), budget)

    assert caught.value.dimension is LocalProfileDimension.INPUT_CELLS
    assert caught.value.attempted == 2
    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_clean(engine)


@pytest.mark.parametrize("safe", [True, False])
def test_wrapped_producer_errors_preserve_only_safe_input_limits(engine, safe: bool) -> None:
    source_error = InputLimitError("synthetic input limit exceeded") if safe else ValueError(CANARY)

    def remaining():
        yield 0, digest(CANARY)
        raise source_error

    expected = InputLimitError if safe else engine.module.DistinctTrackingError
    with pytest.raises(expected) as caught:
        engine.module.count_distinct_stream([set()], remaining(), LocalProfileBudget())

    if safe:
        assert caught.value is source_error
    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_clean(engine)


def test_cleanup_failure_prevents_returning_success(engine, monkeypatch: pytest.MonkeyPatch) -> None:
    original_directory = tempfile.TemporaryDirectory

    class FailedCleanup(original_directory):
        def cleanup(self):
            super().cleanup()
            raise OSError(CANARY)

    monkeypatch.setattr(tempfile, "TemporaryDirectory", FailedCleanup)
    with pytest.raises(engine.module.DistinctTrackingError) as caught:
        engine.module.count_distinct_stream([{digest(CANARY)}], iter(()), LocalProfileBudget())

    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_clean(engine)


def test_native_deadline_applies_after_the_last_producer_batch(engine) -> None:
    consumed = False

    def interrupt_after_producer(record):
        nonlocal consumed
        record.reader.read_all()
        consumed = True
        raise engine.duckdb.InterruptException(CANARY)

    engine.on_query = interrupt_after_producer
    with pytest.raises(LocalProfileLimitError) as caught:
        engine.module.count_distinct_stream(
            [{digest(CANARY)}], iter(()), LocalProfileBudget(),
        )

    assert consumed
    assert caught.value.dimension is LocalProfileDimension.DEADLINE_SECONDS
    assert caught.value.__context__ is None
    assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_clean(engine)


def test_native_query_time_limit_interrupts_counting(engine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine.module, "BATCH_DIGESTS", 1_024)
    budget = LocalProfileBudget()
    monkeypatch.setattr(budget, "remaining_seconds", lambda: 0.02)
    remaining = ((0, digest(f"fictional-distinct-{index}")) for index in range(2_000_000))

    with pytest.raises(LocalProfileLimitError) as caught:
        engine.module.count_distinct_stream([set()], remaining, budget)

    assert caught.value.dimension is LocalProfileDimension.DEADLINE_SECONDS
    assert_clean(engine)


@pytest.mark.parametrize("disk_limit,success", [("2GiB", True), ("1KiB", False)])
def test_real_spill_is_private_keyed_bounded_and_cleaned(
    engine, monkeypatch: pytest.MonkeyPatch, disk_limit: str, success: bool,
) -> None:
    module = engine.module
    monkeypatch.setattr(module, "MEMORY_LIMIT", "16MiB")
    monkeypatch.setattr(module, "TEMP_LIMIT", disk_limit)
    monkeypatch.setattr(module, "BATCH_DIGESTS", 4_096)
    raw_digest = digest(CANARY)
    keys = set()
    original_hmac = module.hmac.digest
    observed_spill = False

    def keyed(key, value, algorithm):
        keys.add(key)
        return original_hmac(key, value, algorithm)

    monkeypatch.setattr(module.hmac, "digest", keyed)

    def remaining():
        nonlocal observed_spill
        for index in range(300_000):
            if not observed_spill and index % 4_096 == 0:
                for record in engine.records:
                    assert stat.S_IMODE(record.path.stat().st_mode) == 0o700
                    for path in record.path.rglob("*"):
                        if path.is_file():
                            payload = path.read_bytes()
                            assert not path.is_symlink()
                            assert CANARY.encode() not in payload
                            assert raw_digest not in payload
                            assert all(key not in payload for key in keys)
                            observed_spill = observed_spill or bool(payload)
            yield 0, digest(f"fictional-distinct-{index}")

    if success:
        assert module.count_distinct_stream(
            [{raw_digest}], remaining(), LocalProfileBudget(),
        ) == [300_001]
        assert observed_spill, "fixture must exercise actual on-disk spill"
    else:
        with pytest.raises(module.DistinctTrackingError) as caught:
            module.count_distinct_stream([{raw_digest}], remaining(), LocalProfileBudget())
        assert caught.value.__context__ is None
        assert CANARY not in "".join(traceback.format_exception(caught.value))
    assert_clean(engine)
