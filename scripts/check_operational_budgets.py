#!/usr/bin/env python3
"""Bounded release regression checks for representative local workloads."""

from __future__ import annotations

import csv
import gc
import json
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeVar

from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.validation import validate_dataset


REPRESENTATIVE_ROWS = 2_500
MAX_PHASE_SECONDS = 15.0
MAX_PHASE_PEAK_BYTES = 256 * 1024 * 1024

T = TypeVar("T")


class OperationalBudgetError(RuntimeError):
    """Raised when a representative workload exceeds a release budget."""


@dataclass(frozen=True)
class PhaseMetrics:
    name: str
    elapsed_seconds: float
    peak_bytes: int


def measure_phase(name: str, operation: Callable[[], T]) -> tuple[T, PhaseMetrics]:
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    try:
        result = operation()
        elapsed = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, PhaseMetrics(name, elapsed, peak_bytes)


def enforce_phase_budget(
    metrics: PhaseMetrics,
    *,
    max_seconds: float = MAX_PHASE_SECONDS,
    max_peak_bytes: int = MAX_PHASE_PEAK_BYTES,
) -> None:
    failures: list[str] = []
    if metrics.elapsed_seconds > max_seconds:
        failures.append(
            f"{metrics.elapsed_seconds:.3f}s exceeds {max_seconds:.3f}s"
        )
    if metrics.peak_bytes > max_peak_bytes:
        failures.append(
            f"{metrics.peak_bytes} peak bytes exceeds {max_peak_bytes}"
        )
    if failures:
        raise OperationalBudgetError(f"{metrics.name}: {', '.join(failures)}")


def write_synthetic_profile_input(folder: Path, row_count: int) -> None:
    folder.mkdir(parents=True)
    with (folder / "customers.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["customer_id", "segment", "active"])
        for index in range(row_count):
            writer.writerow([f"C{index:06d}", f"segment_{index % 8}", index % 2 == 0])

    with (folder / "orders.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["order_id", "customer_id", "amount"])
        for index in range(row_count):
            writer.writerow([f"O{index:06d}", f"C{index:06d}", f"{10 + index % 90}.50"])


def run_operational_budget_check(
    *, row_count: int = REPRESENTATIVE_ROWS
) -> list[PhaseMetrics]:
    with tempfile.TemporaryDirectory(prefix="test-data-agent-budget-") as raw_tmp:
        source = Path(raw_tmp) / "source"
        write_synthetic_profile_input(source, row_count)

        profile, profile_metrics = measure_phase(
            "profile", lambda: profile_example_folder(source, cache_dir=None)
        )
        spec = infer_dataset_spec(profile, count=row_count)
        rows, generation_metrics = measure_phase(
            "generate", lambda: generate_dataset(spec, seed=20260731)
        )
        report, validation_metrics = measure_phase(
            "validate", lambda: validate_dataset(rows, spec)
        )

    if not report.valid:
        raise OperationalBudgetError("representative dataset did not validate")
    expected_counts = {entity.name: row_count for entity in spec.entities}
    observed_counts = {name: len(entity_rows) for name, entity_rows in rows.items()}
    if observed_counts != expected_counts:
        raise OperationalBudgetError(
            f"representative row counts differ: {observed_counts!r}"
        )

    metrics = [profile_metrics, generation_metrics, validation_metrics]
    for phase in metrics:
        enforce_phase_budget(phase)
    return metrics


def main() -> int:
    metrics = run_operational_budget_check()
    print(json.dumps([asdict(metric) for metric in metrics], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
