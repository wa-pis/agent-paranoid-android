#!/usr/bin/env python3
"""Measure unchanged public legacy/streaming CSV bundles on fictional data."""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import ExitStack, contextmanager
import csv
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterator
from unittest.mock import patch

if __package__:
    from .benchmark_parallel_generation import (
        SAMPLE_SECONDS, WORKER_SECONDS, fictional_spec, memory_sample, stop_group,
    )
else:
    from benchmark_parallel_generation import (
        SAMPLE_SECONDS, WORKER_SECONDS, fictional_spec, memory_sample, stop_group,
    )


ROOT = Path(__file__).resolve().parents[1]
CAPS = {
    "TEST_DATA_AGENT_MAX_GENERATION_COUNT": "750000",
    "TEST_DATA_AGENT_MAX_OUTPUT_BYTES": str(4 * 1024**3),
    "TEST_DATA_AGENT_MAX_GENERATION_SECONDS": str(WORKER_SECONDS),
}


class Phases:
    """Exclusive wall time; nested original calls are never counted twice."""

    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        self.clock = clock
        self.seconds: dict[str, float] = defaultdict(float)
        self.calls: dict[str, int] = defaultdict(int)
        self.checked_rows: dict[str, int] = defaultdict(int)
        self.stack = ["setup_and_bookkeeping"]
        self.last = clock()

    def tick(self) -> None:
        now = self.clock()
        self.seconds[self.stack[-1]] += now - self.last
        self.last = now

    def switch(self, name: str) -> None:
        self.tick()
        self.stack[-1] = name

    @contextmanager
    def scope(self, name: str) -> Iterator[None]:
        self.tick()
        self.stack.append(name)
        try:
            yield
        finally:
            self.tick()
            self.stack.pop()

    def wrap(self, original: Callable[..., Any], name: str) -> Callable[..., Any]:
        def measured(*args: Any, **kwargs: Any) -> Any:
            self.calls[name] += 1
            if name in {"mandatory_validation", "report_validation", "combined_validation",
                        "schema_validation", "privacy_validation", "relationship_validation",
                        "constraint_validation", "normalization"}:
                self.checked_rows[name] += sum(len(rows) for rows in args[0].values())
            with self.scope(name):
                return original(*args, **kwargs)
        return measured


class StreamingBudget:
    """Delegate every real budget check; observe existing phase boundaries only."""

    def __init__(self, original: Any, phases: Phases) -> None:
        self.original, self.phases = original, phases
        self.max_seconds = original.max_seconds

    def check(self, phase: str) -> None:
        self.original.check(phase)
        if phase in {"streaming CSV setup", "parallel generation setup"}:
            name = "setup_and_bookkeeping"
        elif phase.startswith("parallel "):
            name = "generation_ipc"
        else:
            name = {
                "streaming CSV validation": "global_checks",
                "streaming CSV encoding": "csv_encoding",
                "streaming CSV write": "csv_write",
                "streaming CSV final validation": "csv_write",
            }.get(phase, self.phases.stack[-1])
        self.phases.switch(name)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.original, name)


@contextmanager
def instrument(phases: Phases) -> Iterator[None]:
    from test_data_agent.generation import entity_generator
    from test_data_agent.io import streaming_csv, workflows, writers
    from test_data_agent.validation import reconciliation

    with ExitStack() as patches:
        for module, attribute, name in [
            (workflows, "generate_dataset", "generation_ipc"),
            (workflows, "_generate_dataset_candidates", "generation_ipc"),
            (entity_generator, "assert_generated_dataset_valid", "mandatory_validation"),
            (workflows, "assert_generated_dataset_valid", "mandatory_validation"),
            (workflows, "validate_dataset", "report_validation"),
            (workflows, "_validate_generated_dataset", "combined_validation"),
            (streaming_csv, "_validate_generated_dataset", "combined_validation"),
            (reconciliation, "validate_schema", "schema_validation"),
            (reconciliation, "validate_generated_row_privacy", "privacy_validation"),
            (reconciliation, "validate_relationships", "relationship_validation"),
            (reconciliation, "validate_constraints", "constraint_validation"),
            (reconciliation, "normalize_dataset_values", "normalization"),
            (workflows, "write_dataset_rows", "csv_write"),
            (writers, "rows_to_csv", "csv_encoding"),
            (writers, "write_bounded_text", "csv_encoding"),
            (writers, "atomic_binary_writer", "csv_write"),
            (workflows, "write_dataset_spec_artifact", "artifacts_and_hashing"),
            (workflows, "write_dataset_validation_report", "artifacts_and_hashing"),
            (workflows, "write_generation_manifest", "artifacts_and_hashing"),
            (workflows, "enforce_output_folder_size", "artifacts_and_hashing"),
            (workflows, "commit_temp_output_folder", "publication"),
        ]:
            patches.enter_context(patch.object(module, attribute, phases.wrap(getattr(module, attribute), name)))
        original_stream = workflows.write_streaming_csv
        original_visit = streaming_csv._visit_generated_tiles

        def stream(*args: Any, **kwargs: Any) -> Any:
            kwargs["budget"] = StreamingBudget(kwargs["budget"], phases)
            with phases.scope("setup_and_bookkeeping"):
                return original_stream(*args, **kwargs)

        def visit(*args: Any, **kwargs: Any) -> Any:
            result = original_visit(*args, **kwargs)
            phases.switch("global_checks")
            return result

        patches.enter_context(patch.object(workflows, "write_streaming_csv", stream))
        patches.enter_context(patch.object(streaming_csv, "_visit_generated_tiles", visit))
        yield


def worker(rows: int, mode: str, output: Path) -> dict[str, Any]:
    from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy
    from test_data_agent.core.settings import OutputFormat
    from test_data_agent.io.workflows import estimate_dataset_output_bytes, generate_dataset_bundle

    spec = fictional_spec(rows)
    policy = ParallelGenerationPolicy(workers=4, max_rows=750_000, max_cells=750_000 * 25)
    estimated = estimate_dataset_output_bytes(spec)
    phases = Phases()
    with instrument(phases):
        started = time.perf_counter()
        phases.last = started
        result = generate_dataset_bundle(
            spec, output_folder=output, output_format=OutputFormat.CSV, seed=42,
            streaming=policy if mode == "streaming" else None,
        )
        phases.tick()
        elapsed = phases.last - started
    assert result.validation.valid and result.synthetic and not result.source_rows_copied
    assert result.row_counts == {"fictional": rows}
    batches = math.ceil(rows / 4096) if mode == "streaming" else 1
    assert phases.calls["mandatory_validation"] == phases.calls["report_validation"] == 0
    for name in ("combined_validation", "schema_validation", "privacy_validation",
                 "relationship_validation", "constraint_validation", "normalization"):
        assert phases.calls[name] == batches
        assert phases.checked_rows[name] == rows
    assert math.isclose(sum(phases.seconds.values()), elapsed, abs_tol=1e-6)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "api_seconds": elapsed, "stage_seconds": dict(phases.seconds),
        "calls": dict(phases.calls), "checked_rows": dict(phases.checked_rows),
        "policy": policy.model_dump() if mode == "streaming" else None,
        "preflight_estimated_bytes": estimated,
        "coordinator_peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
    }


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def audit(output: Path, rows: int, mode: str) -> dict[str, Any]:
    started = time.perf_counter()
    path = output / "fictional.csv"
    csv_sha = digest(path)
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        assert next(reader) == ["row_id", *[f"value_{i}" for i in range(24)]]
        count = 0
        for index, row in enumerate(reader):
            assert len(row) == 25 and int(row[0]) == 42_000_001 + index
            count += 1
        assert count == rows
    validation = json.loads((output / "validation_report.json").read_text())
    assert validation["valid"] and len(validation["sections"]) == 4
    assert {section["name"] for section in validation["sections"]} == {"schema", "relationships", "constraints", "privacy"}
    assert all(section["failed"] == 0 for section in validation["sections"])
    assert all(section["passed"] == 1 for section in validation["sections"]
               if section["name"] != "relationships")
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["synthetic"] and not manifest["source_rows_copied"] and manifest["validation_valid"]
    assert manifest["row_counts"] == {"fictional": rows}
    engine = "tiled-v1" if mode == "streaming" else version("agent-paranoid-android")
    assert manifest["reproducibility"]["generator_algorithm_version"] == engine
    hashes = manifest["reproducibility"]["output_sha256"]
    assert set(hashes) == {"fictional.csv", "dataset_spec.yaml", "validation_report.json"}
    assert {path.name for path in output.iterdir()} == {*hashes, "generation_manifest.json"}
    assert all(digest(output / name) == sha for name, sha in hashes.items())
    assert output.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in output.iterdir())
    return {
        "csv_bytes": path.stat().st_size, "csv_sha256": csv_sha, "engine": engine,
        "exact_header_count_ordered_unique_keys": True, "full_report_valid": True,
        "manifest_and_output_hashes_valid": True, "private_output": True,
        "audit_seconds_outside_measurement": time.perf_counter() - started,
    }


def measure(rows: int, mode: str) -> dict[str, Any]:
    result: dict[str, Any] = {"rows": rows, "mode": mode, "status": "failed"}
    scratch: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="apa-public-csv-benchmark-") as temporary:
            scratch = Path(temporary).resolve()
            assert scratch.stat().st_mode & 0o777 == 0o700
            output = scratch / "out"
            started = time.perf_counter()
            process = subprocess.Popen([
                sys.executable, str(Path(__file__).resolve()), "--worker", mode,
                "--rows", str(rows), "--output", str(output),
            ], env={**os.environ, **CAPS}, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, start_new_session=True)
            peak_tree = peak_coordinator = peak_processes = samples = 0
            try:
                while process.poll() is None:
                    if time.perf_counter() - started > WORKER_SECONDS + 60:
                        raise TimeoutError("bounded benchmark deadline exceeded")
                    total, coordinator, count = memory_sample(process.pid)
                    peak_tree = max(peak_tree, total)
                    peak_coordinator = max(peak_coordinator, coordinator)
                    peak_processes = max(peak_processes, count)
                    samples += 1
                    time.sleep(SAMPLE_SECONDS)
                stdout, stderr = process.communicate(timeout=5)
                result.update(
                    subprocess_seconds=time.perf_counter() - started,
                    sampled_peak_tree_rss_bytes=peak_tree,
                    sampled_peak_coordinator_rss_bytes=peak_coordinator,
                    peak_tree_process_count=peak_processes, memory_samples=samples,
                    returncode=process.returncode, stderr_present=bool(stderr),
                )
                if process.returncode != 0:
                    raise RuntimeError("benchmark worker failed")
                result.update(json.loads(stdout))
            finally:
                stop_group(process)
            result.update(audit(output, rows, mode))
            assert {path.name for path in scratch.iterdir()} == {"out"}
            result.update(status="succeeded", no_partial_staging=True)
    except Exception as error:
        result["error_type"] = type(error).__name__
    finally:
        result["scratch_removed"] = scratch is not None and not scratch.exists()
    return result


def summarize(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for rows, mode in sorted({(run["rows"], run["mode"]) for run in runs}):
        attempts = [run for run in runs if (run["rows"], run["mode"]) == (rows, mode)]
        valid = [run for run in attempts if run["status"] == "succeeded"]
        item: dict[str, Any] = {"rows": rows, "mode": mode, "attempts": len(attempts), "failures": len(attempts) - len(valid)}
        if valid:
            item.update(
                median_api_seconds=statistics.median(run["api_seconds"] for run in valid),
                api_seconds_range=[min(run["api_seconds"] for run in valid), max(run["api_seconds"] for run in valid)],
                max_sampled_peak_tree_rss_bytes=max(run["sampled_peak_tree_rss_bytes"] for run in valid),
                max_coordinator_peak_rss_bytes=max(run["coordinator_peak_rss_bytes"] for run in valid),
                median_stage_seconds={name: statistics.median(run["stage_seconds"].get(name, 0) for run in valid) for name in sorted({key for run in valid for key in run["stage_seconds"]})},
                repeat_csv_identical=len({run["csv_sha256"] for run in valid}) == 1,
            )
        summary.append(item)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, nargs="+", default=[100_000, 750_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reference", type=Path,
                        help="optional completed benchmark from this encoding and generation contract")
    parser.add_argument("--output", type=Path, default=Path("public-csv-results.json"))
    parser.add_argument("--worker", choices=("legacy", "streaming"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not __debug__ or any(not 1 <= rows <= 750_000 for rows in args.rows) or args.repeats < 1:
        parser.error("requires assertions, rows 1..750000 and positive repeats")
    if args.worker:
        print(json.dumps(worker(args.rows[0], args.worker, args.output)))
        return 0
    from test_data_agent.io.path_policy import atomic_write_bytes

    memory_sample(os.getpid())
    baseline_path = args.reference.resolve() if args.reference is not None else None
    baseline = json.loads(baseline_path.read_text()) if baseline_path is not None else None
    assert baseline is None or baseline["completed"]
    reference_runs = ({(run["rows"], run["mode"]): run for run in baseline["runs"]}
                      if baseline is not None else {})
    report: dict[str, Any] = {
        "completed": False,
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform(), "logical_cpus": os.cpu_count(),
                        "dependencies": {name: version(name) for name in ("agent-paranoid-android", "Faker", "pydantic", "PyYAML")}},
        "settings": {"rows": args.rows, "fields": 25, "seed": 42, "repeats": args.repeats,
                     "caps": CAPS, "streaming_workers": 4, "rss_sample_seconds": SAMPLE_SECONDS,
                     "rss_method": "concurrent process-tree ps RSS sum; shared pages may be counted repeatedly",
                     "validation": "all four report sections enabled; all mandatory checks retained",
                     "validation_passes": "combined runner; each concrete validator and normalization once per row/tile",
                     "engine_comparison": "legacy and tiled-v1 differ; require within-engine repeat equality",
                     "storage": tempfile.gettempdir(), "audit_outside_measured_process": True},
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in [
            *sorted((ROOT / "src/test_data_agent").rglob("*.py")), Path(__file__).resolve(),
            ROOT / "scripts/benchmark_parallel_generation.py",
        ]},
        "runs": [],
    }
    if baseline is not None:
        assert baseline_path is not None
        report["baseline"] = {
            "path": str(baseline_path), "sha256": digest(baseline_path),
            "same_dependencies": baseline["environment"]["dependencies"] == report["environment"]["dependencies"],
        }

    def save() -> None:
        atomic_write_bytes(args.output, (json.dumps(report, indent=2) + "\n").encode())

    save()
    for rows in args.rows:
        for repeat in range(args.repeats):
            for mode in (("legacy", "streaming") if repeat % 2 == 0 else ("streaming", "legacy")):
                run = measure(rows, mode)
                reference = reference_runs.get((rows, mode))
                if run["status"] == "succeeded" and reference is not None:
                    run["baseline_csv_identical"] = all(
                        run[key] == reference[key] for key in ("csv_sha256", "csv_bytes")
                    )
                    if not run["baseline_csv_identical"]:
                        run.update(status="failed", error_type="BaselineMismatch")
                run["repeat"] = repeat + 1
                report["runs"].append(run)
                report["summary"] = summarize(report["runs"])
                save()
                print(json.dumps({key: run[key] for key in ("rows", "mode", "repeat", "status", "api_seconds", "sampled_peak_tree_rss_bytes", "error_type") if key in run}), flush=True)
    report["completed"] = all(run["status"] == "succeeded" and run["scratch_removed"] for run in report["runs"]) and all(item["repeat_csv_identical"] for item in report["summary"] if item["failures"] == 0)
    save()
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
