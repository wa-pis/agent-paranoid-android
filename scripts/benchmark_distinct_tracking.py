#!/usr/bin/env python3
"""Compare exact digest counting; synthetic inputs only, never source files.

Run with the project Python plus isolated DuckDB and the existing Parquet extra.
This measures the distinct component, not complete CSV profiling or generation.
Streaming DuckDB query_seconds excludes measured input and Arrow conversion;
query_call_seconds includes that producer work. Use total elapsed for comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Iterator


ENGINES = ("python", "duckdb", "sqlite")


def digest_batches(
    rows: int, columns: int, cardinality: str, batch_rows: int, seed: int,
) -> Iterator[list[tuple[int, bytes]]]:
    domain = rows if cardinality == "unique" else min(100, rows)
    for start in range(0, rows, batch_rows):
        batch = []
        for row in range(start, min(start + batch_rows, rows)):
            for column in range(columns):
                value = f" synthetic-{seed}-{column}-{row % domain} ".strip()
                batch.append((column, hashlib.sha256(value.encode("utf-8")).digest()))
        yield batch


def run_worker(args: argparse.Namespace) -> dict[str, object]:
    started = time.perf_counter()
    cpu_started = time.process_time()
    scratch = Path(args.scratch)
    connection = None
    streaming = args.engine == "duckdb" and args.duckdb_ingestion == "stream"
    if args.engine == "python":
        distinct = [set() for _ in range(args.columns)]
        version = platform.python_version()
    elif args.engine == "sqlite":
        version = sqlite3.sqlite_version
        connection = sqlite3.connect(scratch / "distinct.sqlite")
        # Disposable scratch only: durability adds no value to this workload.
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA cache_size=-131072")
        connection.execute("PRAGMA temp_store=FILE")
        connection.execute(
            "CREATE TABLE digests (column_id INTEGER NOT NULL, digest BLOB NOT NULL, "
            "PRIMARY KEY (column_id, digest)) WITHOUT ROWID"
        )
        connection.execute("BEGIN")
    else:
        import duckdb
        import pyarrow as pa

        version = duckdb.__version__
        database = ":memory:" if streaming else str(scratch / "distinct.duckdb")
        connection = duckdb.connect(database, config={
            "memory_limit": "128MiB",
            "threads": "1",
            "temp_directory": str(scratch / "spill"),
            "autoinstall_known_extensions": "false",
            "autoload_known_extensions": "false",
        })
        try:
            connection.execute("SET enable_external_access = false")
            connection.execute("SET max_temp_directory_size='4GiB'")
            connection.execute("SET preserve_insertion_order=false")
            if not streaming:
                connection.execute("CREATE TABLE digests (column_id INTEGER, digest BLOB)")
                connection.execute("BEGIN")
        except BaseException:
            connection.close()
            raise
    setup_seconds = time.perf_counter() - started
    input_seconds = 0.0
    ingest_seconds = 0.0
    batches = iter(digest_batches(
        args.rows, args.columns, args.cardinality, args.batch_rows, args.seed,
    ))
    if streaming:
        schema = pa.schema([("column_id", pa.int32()), ("digest", pa.binary(32))])

        def arrow_batches():
            nonlocal input_seconds, ingest_seconds
            while True:
                tick = time.perf_counter()
                try:
                    batch = next(batches)
                except StopIteration:
                    return
                input_seconds += time.perf_counter() - tick
                tick = time.perf_counter()
                arrow_batch = pa.RecordBatch.from_arrays([
                    pa.array([c for c, _ in batch], type=pa.int32()),
                    pa.array([d for _, d in batch], type=pa.binary(32)),
                ], schema=schema)
                ingest_seconds += time.perf_counter() - tick
                yield arrow_batch

        tick = time.perf_counter()
        producer_before = input_seconds + ingest_seconds
        reader = pa.RecordBatchReader.from_batches(schema, arrow_batches())
        connection.register("digests", reader)
        setup_seconds += (time.perf_counter() - tick
                          - (input_seconds + ingest_seconds - producer_before))
    while not streaming:
        tick = time.perf_counter()
        try:
            batch = next(batches)
        except StopIteration:
            break
        input_seconds += time.perf_counter() - tick
        tick = time.perf_counter()
        if args.engine == "python":
            for column, digest in batch:
                distinct[column].add(digest)
        elif args.engine == "sqlite":
            connection.executemany("INSERT OR IGNORE INTO digests VALUES (?, ?)", batch)
        else:
            table = pa.table({
                "column_id": pa.array([c for c, _ in batch], type=pa.int32()),
                "digest": pa.array([d for _, d in batch], type=pa.binary(32)),
            })
            connection.register("batch", table)
            connection.execute("INSERT INTO digests SELECT * FROM batch")
            connection.unregister("batch")
        ingest_seconds += time.perf_counter() - tick
    tick = time.perf_counter()
    producer_before = input_seconds + ingest_seconds
    if args.engine == "python":
        counts = [len(values) for values in distinct]
    else:
        if args.engine == "sqlite":
            connection.commit()
            query = "SELECT column_id, count(*) FROM digests GROUP BY column_id"
        else:
            if not streaming:
                connection.execute("COMMIT")
            query = "SELECT column_id, count(DISTINCT digest) FROM digests GROUP BY column_id"
        by_column = dict(connection.execute(query).fetchall())
        counts = [by_column.get(column, 0) for column in range(args.columns)]
    query_call_seconds = time.perf_counter() - tick
    query_seconds = query_call_seconds - (input_seconds + ingest_seconds - producer_before)
    expected = args.rows if args.cardinality == "unique" else min(100, args.rows)
    if counts != [expected] * args.columns:
        raise RuntimeError("exact distinct counts differ from the synthetic fixture")
    tick = time.perf_counter()
    if connection is not None:
        connection.close()
    close_seconds = time.perf_counter() - tick
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "engine": args.engine, "version": version,
        "duckdb_ingestion": args.duckdb_ingestion if args.engine == "duckdb" else None,
        "rows": args.rows, "columns": args.columns,
        "cardinality": args.cardinality, "batch_rows": args.batch_rows,
        "seed": args.seed, "counts": counts,
        "elapsed_seconds": time.perf_counter() - started,
        "cpu_seconds": time.process_time() - cpu_started,
        "setup_seconds": setup_seconds, "input_seconds": input_seconds,
        "ingest_seconds": ingest_seconds, "query_seconds": query_seconds,
        "query_call_seconds": query_call_seconds,
        "ingest_kind": "arrow_conversion" if streaming else "batch_ingestion",
        "close_seconds": close_seconds,
        "peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
    }


def directory_bytes(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        try:
            if entry.is_file():
                total += entry.stat().st_size
        except FileNotFoundError:
            pass
    return total


def run_isolated(args: argparse.Namespace, engine: str, rows: int, cardinality: str) -> dict:
    started = time.perf_counter()
    peak_disk = 0
    with tempfile.TemporaryDirectory(prefix="apa-distinct-") as directory:
        command = [
            sys.executable, str(Path(__file__).resolve()), "--worker",
            "--engine", engine, "--rows", str(rows), "--columns", str(args.columns),
            "--cardinality", cardinality, "--batch-rows", str(args.batch_rows),
            "--seed", str(args.seed), "--scratch", directory,
            "--duckdb-ingestion", args.duckdb_ingestion,
        ]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
            try:
                while child.poll() is None:
                    peak_disk = max(peak_disk, directory_bytes(Path(directory)))
                    if peak_disk > 4 * 1024**3:
                        raise RuntimeError("benchmark scratch exceeded 4 GiB")
                    if time.perf_counter() - started > args.timeout:
                        raise TimeoutError("benchmark worker exceeded its deadline")
                    try:
                        child.communicate(timeout=0.1)
                    except subprocess.TimeoutExpired:
                        pass
                stdout, stderr = child.communicate()
                peak_disk = max(peak_disk, directory_bytes(Path(directory)))
                if child.returncode:
                    raise RuntimeError(f"worker failed ({child.returncode}): {stderr}")
                result = json.loads(stdout)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
    result["wall_seconds"] = time.perf_counter() - started
    result["peak_disk_bytes_sampled"] = peak_disk
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--rows", type=int, nargs="+", default=[10_000, 100_000, 750_000])
    result.add_argument("--columns", type=int, default=25)
    result.add_argument("--repeats", type=int, default=3)
    result.add_argument("--engines", nargs="+", choices=ENGINES, default=list(ENGINES))
    result.add_argument("--cardinalities", nargs="+", choices=("unique", "low"), default=["unique", "low"])
    result.add_argument("--batch-rows", type=int, default=2_000)
    result.add_argument("--seed", type=int, default=1729)
    result.add_argument("--duckdb-ingestion", choices=("table", "stream"), default="stream")
    result.add_argument("--timeout", type=float, default=600.0)
    result.add_argument("--output", type=Path, default=Path("distinct-benchmark.json"))
    result.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--engine", choices=ENGINES, help=argparse.SUPPRESS)
    result.add_argument("--cardinality", choices=("unique", "low"), help=argparse.SUPPRESS)
    result.add_argument("--scratch", help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    if min(*args.rows, args.columns, args.repeats, args.batch_rows, args.timeout) <= 0:
        raise ValueError("benchmark dimensions, repeats and deadline must be positive")
    if args.worker:
        if len(args.rows) != 1 or not args.engine or not args.cardinality or not args.scratch:
            raise ValueError("worker requires one row count, engine, cardinality and scratch directory")
        args.rows = args.rows[0]
        print(json.dumps(run_worker(args), sort_keys=True))
        return 0
    report = {
        "environment": {
            "python": sys.version, "platform": platform.platform(),
            "logical_cpus": os.cpu_count(), "executable": sys.executable,
        },
        "settings": {"duckdb_threads": 1, "duckdb_memory_mib": 128,
                     "duckdb_ingestion": args.duckdb_ingestion,
                     "sqlite_cache_mib": 128, "disk_limit_gib": 4,
                     "disk_sample_seconds": 0.1, "timeout_seconds": args.timeout,
                     "repeats": args.repeats, "seed": args.seed},
        "runs": [],
    }
    for rows in args.rows:
        for cardinality in args.cardinalities:
            for repeat in range(args.repeats):
                order = args.engines[repeat % len(args.engines):] + args.engines[:repeat % len(args.engines)]
                for engine in order:
                    metrics = run_isolated(args, engine, rows, cardinality)
                    metrics["repeat"] = repeat + 1
                    report["runs"].append(metrics)
                    args.output.write_text(json.dumps(report, indent=2) + "\n")
                    print(f"{rows}x{args.columns} {cardinality} {engine} #{repeat + 1}: "
                          f"{metrics['wall_seconds']:.2f}s, "
                          f"RSS {metrics['peak_rss_bytes'] / 1024**2:.1f} MiB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
