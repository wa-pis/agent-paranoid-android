#!/usr/bin/env python3
"""Check complete safe-profile equality and process RSS on synthetic CSV only."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

from test_data_agent.io.artifacts import dataset_profile_fingerprint
from test_data_agent.profiling import LocalProfileBudget, LocalProfileLimits, profile_example_folder
from test_data_agent.profiling import schema_profiler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[10_000, 100_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--rule-sample-rows", type=int, default=50_000)
    parser.add_argument("--output", type=Path, default=Path("full-profile-check.json"))
    parser.add_argument("--worker", choices=("set", "auto"), help=argparse.SUPPRESS)
    parser.add_argument("--source", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if min(*args.rows, args.repeats) < 2:
        raise ValueError("rows and repeats must be at least two")
    if args.worker:
        threshold = (sys.maxsize if args.worker == "set"
                     else schema_profiler.MAX_IN_MEMORY_DISTINCT)
        started = time.perf_counter()
        with patch.object(schema_profiler, "MAX_IN_MEMORY_DISTINCT", threshold):
            profile = profile_example_folder(
                args.source, cache_dir=None, rule_sample_rows=args.rule_sample_rows,
                budget=LocalProfileBudget(LocalProfileLimits(max_seconds=600)),
            )
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print(json.dumps({
            "profile": profile.model_dump(mode="json"),
            "profile_sha256": dataset_profile_fingerprint(profile),
            "profile_seconds": time.perf_counter() - started,
            "peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
        }))
        return 0

    report = {
        "environment": {"python": sys.version, "platform": platform.platform()},
        "settings": {"columns": 25, "rule_sample_rows": args.rule_sample_rows,
                     "profile_deadline_seconds": 600, "repeats": args.repeats,
                     "distinct_transition": schema_profiler.MAX_IN_MEMORY_DISTINCT},
        "runs": [],
    }
    with tempfile.TemporaryDirectory(prefix="test-data-agent-profile-check-") as scratch:
        source = Path(scratch)
        for rows in args.rows:
            with (source / "items.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["row_id", *[f"value_{column}" for column in range(1, 25)]])
                for row in range(rows):
                    # A duplicate after the crossover checks transferred distinct state.
                    value = row if row < rows - 1 else 0
                    writer.writerow([f"v{column:02x}{value:06x}" for column in range(25)])
            expected = None
            for repeat in range(args.repeats):
                for backend in (("set", "auto") if repeat % 2 == 0 else ("auto", "set")):
                    started = time.perf_counter()
                    completed = subprocess.run([
                        sys.executable, str(Path(__file__).resolve()), "--worker", backend,
                        "--source", str(source), "--rule-sample-rows", str(args.rule_sample_rows),
                    ], capture_output=True, text=True, check=True, timeout=660)
                    wall = time.perf_counter() - started
                    result = json.loads(completed.stdout)
                    full_profile = result.pop("profile")
                    if expected is None:
                        expected = full_profile
                    if full_profile != expected:
                        raise RuntimeError("complete profiles differ between set and automatic counting")
                    entity = full_profile["entities"][0]
                    if (entity["row_count"] != rows
                            or entity["fields"][0]["distribution"].get("pool_size") != rows - 1):
                        raise RuntimeError("complete profile lost late duplicate evidence")
                    result.update(rows=rows, backend=backend, repeat=repeat + 1,
                                  wall_seconds=wall, full_profile_equal=True)
                    report["runs"].append(result)
                    args.output.write_text(json.dumps(report, indent=2) + "\n")
                    print(f"{rows}x25 {backend} #{repeat + 1}: {wall:.2f}s, "
                          f"RSS {result['peak_rss_bytes'] / 1024**2:.1f} MiB; full profile equal",
                          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
