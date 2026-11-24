#!/usr/bin/env python3
"""Compare bounded Python/Arrow and DuckDB generation with identical checks."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

from benchmark_parallel_generation import (
    SAMPLE_SECONDS,
    WORKER_SECONDS,
    memory_sample,
    stop_group,
    tree_rss,
)


SOURCE_PATHS = (
    "scripts/benchmark_streaming_generation.py",
    "scripts/streaming_generation.py",
    "scripts/benchmark_parallel_generation.py",
)
MANDATORY_CHECKS = ("unique_primary_keys", "scratch_private", "output_private", "scratch_removed")


def measure(rows: int, backend: str) -> dict[str, Any]:
    started = time.perf_counter()
    process = subprocess.Popen([
        sys.executable, str(Path(__file__).resolve()), "--worker", backend,
        "--rows", str(rows),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    peak_tree = peak_coordinator = peak_processes = samples = 0
    try:
        while process.poll() is None:
            if time.perf_counter() - started > WORKER_SECONDS + 60:
                raise TimeoutError("streaming benchmark exceeded its bounded worker deadline")
            total, coordinator, count = memory_sample(process.pid)
            peak_tree = max(peak_tree, total)
            peak_coordinator = max(peak_coordinator, coordinator)
            peak_processes = max(peak_processes, count)
            samples += 1
            time.sleep(SAMPLE_SECONDS)
        stdout, _ = process.communicate(timeout=5)
        if process.returncode != 0:
            raise RuntimeError("streaming benchmark worker failed; no result is accepted")
        result: dict[str, Any] = json.loads(stdout)
        if (result.get("rows_validated") != rows
                or any(result.get(check) is not True for check in MANDATORY_CHECKS)):
            raise RuntimeError("streaming benchmark mandatory checks failed; no result is accepted")
        result.update(
            rows=rows, workers=4, backend=backend,
            worker_wall_seconds=time.perf_counter() - started,
            sampled_peak_tree_rss_bytes=peak_tree,
            sampled_peak_coordinator_rss_bytes=peak_coordinator,
            peak_tree_process_count=peak_processes, memory_samples=samples,
        )
        return result
    finally:
        stop_group(process)


def save_report(path: Path, report: dict[str, Any]) -> None:
    from test_data_agent.io.path_policy import atomic_write_bytes

    atomic_write_bytes(path, (json.dumps(report, indent=2) + "\n").encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[100_000, 750_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reference", type=Path,
                        help="optional completed materialized benchmark from this generation contract")
    parser.add_argument("--output", type=Path, default=Path("streaming-generation-results.json"))
    parser.add_argument("--worker", choices=("arrow", "duckdb"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if any(not 1 <= count <= 750_000 for count in args.rows) or args.repeats < 1:
        parser.error("rows must be 1..750000 and repeats must be positive")
    if args.worker is not None:
        from streaming_generation import run_streaming_benchmark

        failed = False
        try:
            result = run_streaming_benchmark(args.rows[0], args.worker)
        except Exception:
            failed = True
        if failed:
            print("streaming benchmark worker failed", file=sys.stderr)
            return 1
        print(json.dumps(result))
        return 0
    assert tree_rss(10, [(12, 11, 5), (11, 10, 8), (99, 1, 999), (10, 1, 3)]) == (16, 3, 3)
    assert tree_rss(10, [(99, 1, 999)]) == (0, 0, 0)
    memory_sample(os.getpid())
    root = Path(__file__).resolve().parents[1]
    references: dict[int, tuple[int, str]] = {}
    if args.reference is not None:
        baseline = json.loads(args.reference.read_text())
        assert baseline["completed"]
        for run in baseline["runs"]:
            fingerprint = (run["csv_bytes"], run["csv_sha256"])
            assert run["rows"] not in references or references[run["rows"]] == fingerprint
            references[run["rows"]] = fingerprint
    source_paths = sorted(set(SOURCE_PATHS) | {
        path.relative_to(root).as_posix() for path in (root / "src").rglob("*.py")
    })
    report: dict[str, Any] = {
        "completed": False,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "logical_cpus": os.cpu_count(),
                        "dependencies": {package: version(package) for package in
                                         ("pydantic", "Faker", "pyarrow", "duckdb")}},
        "settings": {"seed": 42, "columns": 25, "workers": 4,
                     "engine": "tiled-v1", "arrow_batch_rows": 4096,
                     "duckdb_memory_limit_bytes": 128 * 1024**2,
                     "duckdb_max_temp_directory_size_bytes": 2 * 1024**3,
                     "duckdb_threads": 1,
                     "duckdb_async_threads": 1,
                     "csv_sink": "shared csv.writer + neutralize_csv_cell, UTF-8/CRLF, atomic file + fsync",
                     "backends": ["arrow", "duckdb"], "repeats": args.repeats,
                     "worker_seconds": WORKER_SECONDS,
                     "rss_sample_interval_seconds": SAMPLE_SECONDS,
                     "rss_method": "concurrent ps RSS sum for coordinator and all descendants",
                     "coordinator_in_addition_to_workers": True,
                     "timing_note": "generation_ipc_pool is parent residual wait/IPC/pool/bookkeeping; worker compute overlaps consumer stages; worker_wall includes interpreter/imports"},
        "source_sha256": {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                          for path in source_paths},
        "source_snapshot": "SHA256 covers benchmark scripts and every src/**/*.py file, including uncommitted changes",
        "checks": {"same_seed_csv_equal": False,
                   "all_mandatory_checks_passed": False,
                   "matches_materialized_reference_for_requested_sizes": False},
        "runs": [],
    }
    save_report(args.output, report)
    for rows in args.rows:
        expected = None
        for repeat in range(args.repeats):
            order = ("arrow", "duckdb") if repeat % 2 == 0 else ("duckdb", "arrow")
            for backend in order:
                result = measure(rows, backend)
                fingerprint = (result["csv_bytes"], result["csv_sha256"])
                if expected is None:
                    expected = fingerprint
                if fingerprint != expected:
                    raise RuntimeError("seeded streaming CSV differs between backends or repetitions")
                reference = references.get(rows)
                if reference is not None and fingerprint != reference:
                    raise RuntimeError("streaming CSV differs from the full materialized reference")
                result["materialized_reference_matched"] = reference is not None
                result["repeat"] = repeat + 1
                report["runs"].append(result)
                save_report(args.output, report)
                print(f"{rows}x25 {backend} #{repeat + 1}: {result['total_seconds']:.2f}s, "
                      f"sampled tree RSS {result['sampled_peak_tree_rss_bytes'] / 1024**2:.1f} MiB; "
                      "CSV equal", flush=True)
    report["checks"]["same_seed_csv_equal"] = True
    report["checks"]["all_mandatory_checks_passed"] = True
    report["checks"]["matches_materialized_reference_for_requested_sizes"] = all(
        rows in references for rows in args.rows)
    report["completed"] = True
    save_report(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
