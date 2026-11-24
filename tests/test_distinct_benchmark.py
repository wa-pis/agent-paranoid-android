from __future__ import annotations

from pathlib import Path

import pytest

from scripts import benchmark_distinct_tracking as benchmark


def test_digest_batches_are_deterministic_and_bounded() -> None:
    batches = list(benchmark.digest_batches(13, 3, "unique", 4, 1729))

    assert batches == list(benchmark.digest_batches(13, 3, "unique", 4, 1729))
    assert batches != list(benchmark.digest_batches(13, 3, "unique", 4, 1730))
    assert [len(batch) for batch in batches] == [12, 12, 12, 3]
    assert all(isinstance(digest, bytes) and len(digest) == 32
               for batch in batches for _, digest in batch)
    for column in range(3):
        assert len({digest for batch in batches for field, digest in batch
                    if field == column}) == 13


def test_low_cardinality_duplicates_cross_batch_boundaries() -> None:
    batches = list(benchmark.digest_batches(203, 3, "low", 37, 1729))
    flattened = [entry for batch in batches for entry in batch]

    assert flattened[100 * 3:101 * 3] == flattened[:3]
    assert flattened[200 * 3:201 * 3] == flattened[:3]
    for column in range(3):
        assert len({digest for field, digest in flattened if field == column}) == 100


@pytest.mark.parametrize("engine,ingestion", [
    ("python", "stream"), ("sqlite", "stream"),
    ("duckdb", "table"), ("duckdb", "stream"),
])
@pytest.mark.parametrize("cardinality,expected", [("unique", 203), ("low", 100)])
def test_workers_count_every_column_exactly(
    tmp_path: Path, engine: str, ingestion: str, cardinality: str, expected: int,
) -> None:
    if engine == "duckdb":
        pytest.importorskip("duckdb")
        pytest.importorskip("pyarrow")
    args = benchmark.parser().parse_args([
        "--worker", "--engine", engine, "--rows", "203", "--columns", "3",
        "--cardinality", cardinality, "--batch-rows", "37", "--scratch", str(tmp_path),
        "--duckdb-ingestion", ingestion,
    ])
    args.rows = args.rows[0]

    result = benchmark.run_worker(args)

    assert result["engine"] == engine
    assert result["duckdb_ingestion"] == (ingestion if engine == "duckdb" else None)
    assert result["counts"] == [expected] * 3
    assert result["peak_rss_bytes"] > 0
    assert result["elapsed_seconds"] > 0
    assert result["cpu_seconds"] > 0
    assert all(result[name] >= 0 for name in (
        "setup_seconds", "input_seconds", "ingest_seconds", "query_seconds", "close_seconds",
    ))
    assert result["query_call_seconds"] >= result["query_seconds"]


def test_streaming_duckdb_consumes_lazy_input_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    duckdb = pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    original_batches = benchmark.digest_batches
    original_connect = duckdb.connect
    produced_batches = 0
    readers = []

    def tracked_batches(*args):
        nonlocal produced_batches
        for batch in original_batches(*args):
            produced_batches += 1
            yield batch

    class ObservingConnection:
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def register(self, name, reader):
            assert produced_batches == 0
            readers.append(reader)
            return self.connection.register(name, reader)

        def close(self):
            with pytest.raises(StopIteration):
                readers[0].read_next_batch()
            self.connection.close()

    monkeypatch.setattr(benchmark, "digest_batches", tracked_batches)
    monkeypatch.setattr(duckdb, "connect", lambda *args, **kwargs:
                        ObservingConnection(original_connect(*args, **kwargs)))
    args = benchmark.parser().parse_args([
        "--engine", "duckdb", "--duckdb-ingestion", "stream", "--rows", "203",
        "--columns", "3", "--batch-rows", "37", "--cardinality", "low",
        "--scratch", str(tmp_path),
    ])
    args.rows = args.rows[0]

    assert benchmark.run_worker(args)["counts"] == [100] * 3
    assert produced_batches == 6
    assert len(readers) == 1


@pytest.mark.parametrize("engine", ["python", "sqlite"])
def test_isolated_run_reports_process_metrics(engine: str) -> None:
    args = benchmark.parser().parse_args(["--columns", "3", "--batch-rows", "37"])

    result = benchmark.run_isolated(args, engine, 203, "low")

    assert result["counts"] == [100] * 3
    assert result["wall_seconds"] >= result["elapsed_seconds"] > 0
    assert result["peak_rss_bytes"] > 0
    assert (result["peak_disk_bytes_sampled"] > 0) == (engine == "sqlite")


def test_isolated_timeout_cleans_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = benchmark.parser().parse_args(["--timeout", "0.000000001"])
    monkeypatch.setattr(benchmark.tempfile, "tempdir", str(tmp_path))

    with pytest.raises(TimeoutError, match="deadline"):
        benchmark.run_isolated(args, "python", 750_000, "unique")

    assert list(tmp_path.iterdir()) == []
