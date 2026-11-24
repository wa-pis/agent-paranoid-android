#!/usr/bin/env python3
"""Compare 1/2/4 generation workers on fictional data, with whole-tree RSS."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from test_data_agent.core.dataset import DatasetSpec


SAMPLE_SECONDS = 0.1
WORKER_SECONDS = 600


def tree_rss(root: int, snapshot: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Sum concurrent RSS, including every descendant and the coordinator."""
    members = {root}
    while True:
        expanded = members | {pid for pid, parent, _ in snapshot if parent in members}
        if expanded == members:
            break
        members = expanded
    selected = [(pid, rss) for pid, _, rss in snapshot if pid in members]
    return (sum(rss for _, rss in selected),
            next((rss for pid, rss in selected if pid == root), 0), len(selected))


def memory_sample(root: int) -> tuple[int, int, int]:
    completed = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True,
        check=True, timeout=5,
    )
    snapshot = []
    for line in completed.stdout.splitlines():
        pid, parent, kib = map(int, line.split())
        snapshot.append((pid, parent, kib * 1024))
    return tree_rss(root, snapshot)


def fictional_spec(rows: int) -> DatasetSpec:
    """The shared synthetic fixture used by the materialized and streaming runs."""
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.core.entity import EntitySpec
    from test_data_agent.core.field import FieldSpec

    cases: list[tuple[str, dict[str, Any]]] = [
        ("integer", {"kind": "numeric", "min_value": 1, "max_value": 1000}),
        ("float", {"kind": "numeric", "min_value": 1, "max_value": 1000}),
        ("boolean", {"kind": "boolean", "true_ratio": 0.4}),
        ("date", {"kind": "date_range", "min": "2020-01-01", "max": "2025-01-01"}),
        ("string", {"kind": "categorical", "categories": [
            {"value": "synthetic_alpha", "count": 3},
            {"value": "synthetic_beta", "count": 2},
            {"value": "synthetic_gamma", "count": 1},
        ]}),
        ("string", {"kind": "string_pattern", "min_length": 16, "max_length": 24}),
    ]
    fields: list[dict[str, Any]] = [{"name": "row_id", "data_type": "integer", "is_identifier": True}]
    for index in range(24):
        data_type, distribution = cases[index % len(cases)]
        fields.append({"name": f"value_{index}", "data_type": data_type,
                       "distribution": distribution})
    return DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=rows, primary_key="row_id",
        fields=[FieldSpec.model_validate(field) for field in fields],
    )])


def worker(rows: int, workers: int) -> dict[str, Any]:
    from test_data_agent.adapters.parallel_generation import (
        ParallelGenerationPolicy,
        generate_dataset_parallel,
    )
    from test_data_agent.core.limits import GenerationBudget, enforce_output_payload_size
    from test_data_agent.generation.tiled_generator import ENGINE_VERSION, TILE_ROWS
    from test_data_agent.io.writers import rows_to_csv

    spec = fictional_spec(rows)
    policy = ParallelGenerationPolicy(workers=workers, max_rows=rows, max_cells=rows * 25)
    started = time.perf_counter()
    data = generate_dataset_parallel(spec, seed=42, policy=policy,
                                     budget=GenerationBudget(WORKER_SECONDS))
    generated = time.perf_counter()
    records = data["fictional"]
    if len(records) != rows or any(row["row_id"] != 42_000_001 + index
                                   for index, row in enumerate(records)):
        raise RuntimeError("generated row count or unique global key range differs")
    verified = time.perf_counter()
    csv = rows_to_csv(records)
    serialized = time.perf_counter()
    encoded = csv.encode()
    enforce_output_payload_size(len(encoded), label="benchmark CSV")
    digest = hashlib.sha256(encoded).hexdigest()
    hashed = time.perf_counter()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "engine": ENGINE_VERSION, "tile_rows": TILE_ROWS, "policy": policy.model_dump(),
        "generation_validation_seconds": generated - started,
        "verification_seconds": verified - generated,
        "csv_serialization_seconds": serialized - verified,
        "csv_hash_seconds": hashed - serialized,
        "total_seconds": generated - started + hashed - verified,
        "csv_bytes": len(encoded), "csv_sha256": digest, "unique_primary_keys": True,
        "coordinator_peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
    }


def stop_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        process.wait(timeout=5)
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            process.wait(timeout=5)
            return
        time.sleep(0.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def measure(rows: int, workers: int) -> dict[str, Any]:
    started = time.perf_counter()
    process = subprocess.Popen([
        sys.executable, str(Path(__file__).resolve()), "--worker", str(workers),
        "--rows", str(rows),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    peak_tree = peak_coordinator = peak_processes = samples = 0
    try:
        while process.poll() is None:
            if time.perf_counter() - started > WORKER_SECONDS + 60:
                raise TimeoutError("benchmark exceeded its bounded worker deadline")
            total, coordinator, count = memory_sample(process.pid)
            peak_tree = max(peak_tree, total)
            peak_coordinator = max(peak_coordinator, coordinator)
            peak_processes = max(peak_processes, count)
            samples += 1
            time.sleep(SAMPLE_SECONDS)
        stdout, _ = process.communicate(timeout=5)
        if process.returncode != 0:
            raise RuntimeError("benchmark worker failed; no result is accepted")
        result: dict[str, Any] = json.loads(stdout)
        result.update(
            rows=rows, workers=workers, worker_wall_seconds=time.perf_counter() - started,
            sampled_peak_tree_rss_bytes=peak_tree,
            sampled_peak_coordinator_rss_bytes=peak_coordinator,
            peak_tree_process_count=peak_processes, memory_samples=samples,
        )
        return result
    finally:
        stop_group(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[100_000, 750_000])
    parser.add_argument("--workers", nargs="+", type=int, choices=(1, 2, 4), default=[1, 2, 4])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("parallel-generation-results.json"))
    parser.add_argument("--worker", type=int, choices=(1, 2, 4), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if any(not 1 <= count <= 750_000 for count in args.rows) or args.repeats < 1:
        parser.error("rows must be 1..750000 and repeats must be positive")
    if args.worker is not None:
        print(json.dumps(worker(args.rows[0], args.worker)))
        return 0
    assert tree_rss(10, [(12, 11, 5), (11, 10, 8), (99, 1, 999), (10, 1, 3)]) == (16, 3, 3)
    assert tree_rss(10, [(99, 1, 999)]) == (0, 0, 0)
    memory_sample(os.getpid())
    report: dict[str, Any] = {
        "completed": False,
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "logical_cpus": os.cpu_count(),
                        "dependencies": {package: version(package) for package in ("pydantic", "Faker")}},
        "settings": {"seed": 42, "columns": 25, "repeats": args.repeats,
                     "workers": args.workers, "worker_seconds": WORKER_SECONDS,
                     "rss_sample_interval_seconds": SAMPLE_SECONDS,
                     "rss_method": "concurrent ps RSS sum for coordinator and all descendants",
                     "coordinator_in_addition_to_workers": True,
                     "dataset_temp_disk_bytes": 0},
        "source_sha256": {path: hashlib.sha256(
            (Path(__file__).resolve().parents[1] / path).read_bytes()).hexdigest()
            for path in ("src/test_data_agent/adapters/parallel_generation.py",
                         "src/test_data_agent/generation/tiled_generator.py",
                         "src/test_data_agent/generation/entity_generator.py",
                         "src/test_data_agent/validation/schema_validator.py",
                         "scripts/benchmark_parallel_generation.py")},
        "runs": [],
    }
    for rows in args.rows:
        expected = None
        for repeat in range(args.repeats):
            order = args.workers[repeat % len(args.workers):] + args.workers[:repeat % len(args.workers)]
            for workers in order:
                result = measure(rows, workers)
                if expected is None:
                    expected = result["csv_sha256"]
                if result["csv_sha256"] != expected:
                    raise RuntimeError("seeded CSV differs between process counts or repetitions")
                result["repeat"] = repeat + 1
                report["runs"].append(result)
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                print(f"{rows}x25 {workers} workers #{repeat + 1}: "
                      f"{result['total_seconds']:.2f}s, sampled tree RSS "
                      f"{result['sampled_peak_tree_rss_bytes'] / 1024**2:.1f} MiB; CSV equal", flush=True)
    report["completed"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
