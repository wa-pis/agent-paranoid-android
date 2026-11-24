#!/usr/bin/env python3
"""Pair unchanged public CSV benchmarks around generation type dispatch."""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
from typing import Any

if __package__:
    from . import benchmark_paired_csv as paired
else:
    import benchmark_paired_csv as paired


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = "src/test_data_agent/generation/entity_generator.py"
REFERENCE = "paired-results.json"


def snapshots(
    root: Path, before_source: Path,
) -> tuple[dict[str, Path], dict[str, dict[str, str]]]:
    paths = {arm: root / arm for arm in ("before", "after")}
    for arm, source in (("before", before_source), ("after", ROOT)):
        path = paths[arm]
        shutil.copytree(source / "src/test_data_agent", path / "src/test_data_agent",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (path / "scripts").mkdir()
        for name in paired.HELPERS:
            shutil.copyfile(source / name, path / name)
    hashes = {arm: paired.fingerprints(path) for arm, path in paths.items()}
    assert hashes["before"].keys() == hashes["after"].keys()
    assert [name for name in hashes["before"]
            if hashes["before"][name] != hashes["after"][name]] == [GENERATOR]
    return paths, hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-source", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True,
                        help="completed paired benchmark matching the before-source fingerprint")
    parser.add_argument("--rows", type=int, nargs="+", default=[100_000, 750_000])
    parser.add_argument("--pairs", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (not __debug__ or args.pairs < 2 or args.pairs % 2
            or len(set(args.rows)) != len(args.rows)
            or any(not 1 <= rows <= 750_000 for rows in args.rows)):
        parser.error("requires assertions, distinct rows 1..750000 and an even positive pair count")
    from test_data_agent.io.path_policy import atomic_write_bytes

    benchmark = paired.benchmark
    benchmark.memory_sample(os.getpid())
    before_source = args.before_source.resolve()
    assert not args.output.resolve().is_relative_to(before_source), "before source must remain read-only"
    input_hashes = paired.fingerprints(before_source)
    reference_path = ROOT / args.reference
    reference_hash = benchmark.digest(reference_path)
    reference = json.loads(reference_path.read_text())
    assert reference["completed"] and input_hashes == reference["source_sha256"]["after"]
    references: dict[tuple[int, str], set[tuple[str, int]]] = {}
    for run in reference["runs"]:
        assert run["status"] == "succeeded"
        references.setdefault((run["rows"], run["mode"]), set()).add(
            (run["csv_sha256"], run["csv_bytes"]))
    assert all(len(values) == 1 for values in references.values())
    assert all((rows, mode) in references for rows in args.rows for mode in ("legacy", "streaming"))
    environment = {
        "python": sys.version, "executable": sys.executable,
        "platform": platform.platform(), "logical_cpus": os.cpu_count(),
        "dependencies": {name: version(name) for name in
                         ("agent-paranoid-android", "Faker", "pydantic", "PyYAML")},
    }
    assert environment["dependencies"] == reference["environment"]["dependencies"]
    report: dict[str, Any] = {
        "completed": False, "environment": environment,
        "settings": {
            "rows": args.rows, "fields": 25, "seed": 42, "pairs": args.pairs,
            "order": "adjacent AB/BA pairs; mode order also alternates",
            "caps": benchmark.CAPS, "streaming_workers": 4,
            "rss_sample_seconds": benchmark.SAMPLE_SECONDS,
            "rss_method": "unchanged concurrent ps process-tree RSS sum; shared pages may count repeatedly",
            "pythonhashseed": 0, "bytecode_cache": False,
            "checks": "unchanged measure/worker/instrument/audit; full validation and output audits",
            "audit_outside_measured_process": True,
            "decision_rule": "Retain only with equivalent values/states and repeatable generation gains without a consistent material API-time or peak-memory regression; streaming generation/IPC is exposed coordinator time.",
        },
        "driver_sha256": benchmark.digest(Path(__file__)),
        "paired_driver_sha256": benchmark.digest(Path(paired.__file__)),
        "baseline": {"path": str(args.reference), "sha256": reference_hash,
                     "source_arm": "after", "same_dependencies": True},
        "before_source": str(before_source), "smoke_runs": [], "runs": [],
    }

    def save() -> None:
        atomic_write_bytes(args.output, (json.dumps(report, indent=2) + "\n").encode())

    with tempfile.TemporaryDirectory(prefix="apa-generation-dispatch-") as temporary:
        scratch = Path(temporary).resolve()
        assert scratch.stat().st_mode & 0o777 == 0o700
        paths, hashes = snapshots(scratch, before_source)
        assert hashes["before"] == input_hashes
        report["source_sha256"] = hashes
        save()

        def measure(arm: str, rows: int, mode: str) -> dict[str, Any]:
            if paired.fingerprints(paths[arm]) != hashes[arm]:
                return {"rows": rows, "mode": mode, "status": "failed",
                        "error_type": "SnapshotMismatch", "scratch_removed": True}
            run = paired.measure(paths[arm], rows, mode)
            if run["status"] == "succeeded":
                run["source_verified"] = run["writer_sha256"] == hashes[arm][paired.WRITER]
                if not run["source_verified"]:
                    run.update(status="failed", error_type="EvidenceMismatch")
            return run

        for mode in ("legacy", "streaming"):
            for arm in ("before", "after"):
                run = {**measure(arm, 4, mode), "arm": arm}
                report["smoke_runs"].append(run)
                save()
        smoke_ok = (
            all(run["status"] == "succeeded" and run["scratch_removed"]
                for run in report["smoke_runs"])
            and all(len({(run["csv_sha256"], run["csv_bytes"])
                         for run in report["smoke_runs"] if run["mode"] == mode}) == 1
                    for mode in ("legacy", "streaming"))
        )
        if smoke_ok:
            for rows, mode, pair, arm in paired.schedule(args.rows, args.pairs):
                run = {**measure(arm, rows, mode), "pair": pair, "arm": arm}
                if run["status"] == "succeeded":
                    run["baseline_csv_identical"] = (
                        run["csv_sha256"], run["csv_bytes"]) in references[(rows, mode)]
                    if not run["baseline_csv_identical"]:
                        run.update(status="failed", error_type="EvidenceMismatch")
                report["runs"].append(run)
                report["summary"] = paired.summarize(report["runs"])
                save()
                print(json.dumps({key: run[key] for key in (
                    "rows", "mode", "pair", "arm", "status", "api_seconds",
                    "sampled_peak_tree_rss_bytes", "error_type",
                ) if key in run}), flush=True)
        report["snapshots_unchanged"] = all(paired.fingerprints(paths[arm]) == hashes[arm] for arm in paths)
    report["snapshot_scratch_removed"] = not scratch.exists()
    report["before_source_unchanged"] = paired.fingerprints(before_source) == input_hashes
    report["baseline_unchanged"] = benchmark.digest(reference_path) == reference_hash
    report["completed"] = (
        smoke_ok and len(report["runs"]) == len(args.rows) * 2 * args.pairs * 2
        and all(run["status"] == "succeeded" and run["scratch_removed"] for run in report["runs"])
        and all(item["all_csv_identical"] and len(item["pairs"]) == args.pairs
                for item in report["summary"])
        and report["snapshots_unchanged"] and report["snapshot_scratch_removed"]
        and report["before_source_unchanged"] and report["baseline_unchanged"]
    )
    save()
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
