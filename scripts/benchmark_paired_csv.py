#!/usr/bin/env python3
"""Pair unchanged public CSV benchmarks around the two-line encoding guard."""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any, Iterator

if __package__:
    from . import benchmark_public_csv as benchmark
else:
    import benchmark_public_csv as benchmark


ROOT = Path(__file__).resolve().parents[1]
GUARD = '    if type(value) is str and value[0] not in " \\t\\r\\n=+-@":\n        return value\n'
WRITER = "src/test_data_agent/io/writers.py"
HELPERS = ("scripts/benchmark_public_csv.py", "scripts/benchmark_parallel_generation.py")
DECISION_RULE = (
    "Retain only if paired encoding gains repeat without a consistent API-time or "
    "peak-memory regression; consider individual pairs and AB/BA order, not historical medians."
)
HELPER = """
import json, sys
from pathlib import Path
import benchmark_public_csv as benchmark
import test_data_agent
from test_data_agent.adapters import parallel_generation
from test_data_agent.io import streaming_csv, workflows, writers
root = Path(sys.argv[1]).resolve()
modules = (benchmark, test_data_agent, parallel_generation, streaming_csv, workflows, writers)
origins = {module.__name__: str(Path(module.__file__).resolve().relative_to(root)) for module in modules}
assert streaming_csv.encode_csv_cell is writers.encode_csv_cell
result = benchmark.measure(int(sys.argv[2]), sys.argv[3])
result['import_origins'] = origins
result['writer_sha256'] = benchmark.digest(Path(writers.__file__))
print(json.dumps(result))
"""


def fingerprints(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): benchmark.digest(path) for path in [
        *sorted((root / "src/test_data_agent").rglob("*.py")),
        *(root / name for name in HELPERS),
    ]}


def snapshots(root: Path) -> tuple[dict[str, Path], dict[str, dict[str, str]]]:
    paths = {arm: root / arm for arm in ("before", "after")}
    for path in paths.values():
        shutil.copytree(ROOT / "src/test_data_agent", path / "src/test_data_agent",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (path / "scripts").mkdir()
        for name in HELPERS:
            shutil.copyfile(ROOT / name, path / name)
    before = paths["before"] / WRITER
    text = before.read_text()
    assert text.count(GUARD) == 1, "requires exactly the measured CSV guard"
    before.write_text(text.replace(GUARD, "", 1))
    hashes = {arm: fingerprints(path) for arm, path in paths.items()}
    assert hashes["before"].keys() == hashes["after"].keys()
    assert [name for name in hashes["before"]
            if hashes["before"][name] != hashes["after"][name]] == [WRITER]
    return paths, hashes


def schedule(rows: list[int], pairs: int) -> Iterator[tuple[int, str, int, str]]:
    for count in rows:
        for pair in range(1, pairs + 1):
            modes = ("legacy", "streaming") if pair % 2 else ("streaming", "legacy")
            arms = ("before", "after") if pair % 2 else ("after", "before")
            for mode in modes:
                for arm in arms:
                    yield count, mode, pair, arm


def measure(path: Path, rows: int, mode: str) -> dict[str, Any]:
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([
        str(path / "src"), str(path / "scripts"),
    ]), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    completed = subprocess.run(
        [sys.executable, "-c", HELPER, str(path), str(rows), mode],
        cwd=path, env=environment, capture_output=True, text=True,
    )
    if completed.returncode:
        return {"rows": rows, "mode": mode, "status": "failed",
                "returncode": completed.returncode, "error_type": "HelperFailure",
                "stderr_present": bool(completed.stderr), "scratch_removed": False}
    return json.loads(completed.stdout)


def summarize(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for rows, mode in sorted({(run["rows"], run["mode"]) for run in runs}):
        case = [run for run in runs if (run["rows"], run["mode"]) == (rows, mode)]
        arms = {arm: benchmark.summarize([run for run in case if run["arm"] == arm])
                for arm in ("before", "after")}
        pairs = []
        stage_changes: dict[str, list[float]] = {}
        for number in sorted({run["pair"] for run in case}):
            attempts = [run for run in case if run["pair"] == number]
            if len(attempts) != 2 or any(run["status"] != "succeeded" for run in attempts):
                continue
            before, after = (next(run for run in attempts if run["arm"] == arm)
                             for arm in ("before", "after"))
            item = {"pair": number, "order": [run["arm"] for run in attempts]}
            for metric in ("api_seconds", "sampled_peak_tree_rss_bytes", "coordinator_peak_rss_bytes"):
                item[metric + "_delta"] = after[metric] - before[metric]
                item[metric + "_percent_change"] = 100 * (after[metric] / before[metric] - 1)
            item["csv_encoding_seconds_delta"] = after["stage_seconds"]["csv_encoding"] - before["stage_seconds"]["csv_encoding"]
            for name, value in before["stage_seconds"].items():
                if value > 0:
                    stage_changes.setdefault(name, []).append(
                        100 * (after["stage_seconds"].get(name, 0) / value - 1))
            pairs.append(item)
        valid = [run for run in case if run["status"] == "succeeded"]
        summaries.append({
            "rows": rows, "mode": mode, "arms": arms, "pairs": pairs,
            "all_csv_identical": bool(valid) and len({(run["csv_sha256"], run["csv_bytes"]) for run in valid}) == 1,
            "median_paired_percent_change": {
                key: statistics.median(item[key] for item in pairs)
                for key in pairs[0] if key.endswith("_percent_change")
            } if pairs else {},
            "median_paired_stage_percent_change": {
                name: statistics.median(values) for name, values in stage_changes.items()},
        })
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, nargs="+", default=[100_000, 750_000])
    parser.add_argument("--pairs", type=int, default=4)
    parser.add_argument("--reference", type=Path,
                        help="optional completed CSV benchmark with this generation contract")
    parser.add_argument("--historical-root", type=Path,
                        help="optional original evidence directory; requires matching source fingerprints")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (not __debug__ or args.pairs < 2 or args.pairs % 2
            or len(set(args.rows)) != len(args.rows)
            or any(not 1 <= rows <= 750_000 for rows in args.rows)):
        parser.error("requires assertions, distinct rows 1..750000 and an even positive pair count")
    from test_data_agent.io.path_policy import atomic_write_bytes

    benchmark.memory_sample(os.getpid())
    baseline_path = args.reference.resolve() if args.reference is not None else None
    baseline = json.loads(baseline_path.read_text()) if baseline_path is not None else None
    assert baseline is None or baseline["completed"]
    references = ({(run["rows"], run["mode"]): run for run in baseline["runs"]}
                  if baseline is not None else {})
    report: dict[str, Any] = {
        "completed": False,
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform(), "logical_cpus": os.cpu_count(),
                        "dependencies": {name: version(name) for name in ("agent-paranoid-android", "Faker", "pydantic", "PyYAML")}},
        "settings": {"rows": args.rows, "fields": 25, "seed": 42, "pairs": args.pairs,
                     "order": "adjacent AB/BA pairs; mode order also alternates",
                     "caps": benchmark.CAPS, "streaming_workers": 4,
                     "rss_sample_seconds": benchmark.SAMPLE_SECONDS,
                     "rss_method": "unchanged concurrent ps process-tree RSS sum; shared pages may count repeatedly",
                     "pythonhashseed": 0, "bytecode_cache": False,
                     "checks": "unchanged measure/worker/instrument/audit; full validation and output audits",
                     "audit_outside_measured_process": True, "decision_rule": DECISION_RULE},
        "driver_sha256": benchmark.digest(Path(__file__)),
        "baseline": ({"path": str(baseline_path), "sha256": benchmark.digest(baseline_path)}
                     if baseline_path is not None else None),
        "smoke_runs": [], "runs": [],
    }

    def save() -> None:
        atomic_write_bytes(args.output, (json.dumps(report, indent=2) + "\n").encode())

    with tempfile.TemporaryDirectory(prefix="apa-paired-csv-") as temporary:
        scratch = Path(temporary).resolve()
        assert scratch.stat().st_mode & 0o777 == 0o700
        paths, hashes = snapshots(scratch)
        report["source_sha256"] = hashes
        report["historical_sources"] = {}
        for arm, folder in (("before", "value-normalization-performance"),
                            ("after", "csv-encoding-performance")):
            if args.historical_root is None:
                continue
            path = args.historical_root / folder / "public-csv-results.json"
            historical = json.loads(path.read_text())
            matches = hashes[arm] == historical["source_sha256"]
            assert historical["completed"] and matches
            report["historical_sources"][arm] = {
                "path": str(path), "sha256": benchmark.digest(path),
                "all_source_hashes_equal": matches,
                "same_dependencies": historical["environment"]["dependencies"] == report["environment"]["dependencies"],
            }
        for mode in ("legacy", "streaming"):
            for arm in ("before", "after"):
                run = measure(paths[arm], 4, mode)
                assert run["status"] == "succeeded" and run["scratch_removed"]
                assert run["writer_sha256"] == hashes[arm][WRITER]
                report["smoke_runs"].append({**run, "arm": arm})
            assert report["smoke_runs"][-1]["csv_sha256"] == report["smoke_runs"][-2]["csv_sha256"]
        save()
        for rows, mode, pair, arm in schedule(args.rows, args.pairs):
            assert fingerprints(paths[arm]) == hashes[arm]
            run = {**measure(paths[arm], rows, mode), "pair": pair, "arm": arm}
            reference = references.get((rows, mode))
            if run["status"] == "succeeded":
                run["source_verified"] = run["writer_sha256"] == hashes[arm][WRITER]
                run["baseline_csv_identical"] = reference is None or all(
                    run[key] == reference[key] for key in ("csv_sha256", "csv_bytes"))
                if not run["source_verified"] or not run["baseline_csv_identical"]:
                    run.update(status="failed", error_type="EvidenceMismatch")
            report["runs"].append(run)
            report["summary"] = summarize(report["runs"])
            save()
            print(json.dumps({key: run[key] for key in (
                "rows", "mode", "pair", "arm", "status", "api_seconds", "sampled_peak_tree_rss_bytes", "error_type",
            ) if key in run}), flush=True)
        report["snapshots_unchanged"] = all(fingerprints(paths[arm]) == hashes[arm] for arm in paths)
    report["snapshot_scratch_removed"] = not scratch.exists()
    report["completed"] = (
        len(report["runs"]) == len(args.rows) * 2 * args.pairs * 2
        and all(run["status"] == "succeeded" and run["scratch_removed"] for run in report["runs"])
        and all(item["all_csv_identical"] and len(item["pairs"]) == args.pairs for item in report["summary"])
        and report["snapshots_unchanged"] and report["snapshot_scratch_removed"]
    )
    save()
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
