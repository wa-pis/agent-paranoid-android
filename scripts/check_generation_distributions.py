#!/usr/bin/env python3
"""Compare two source checkouts using fictional generation, validation and CSV."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
from typing import Any


def worker(source: Path, rows: int) -> dict[str, Any]:
    sys.path.insert(0, str(source.resolve()))
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.core.entity import EntitySpec
    from test_data_agent.core.field import FieldSpec
    from test_data_agent.generation.entity_generator import generate_dataset
    from test_data_agent.io.writers import rows_to_csv

    if not Path(generate_dataset.__code__.co_filename).resolve().is_relative_to(source.resolve()):
        raise RuntimeError("worker imported generation from the wrong source")

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
    spec = DatasetSpec(entities=[EntitySpec(
        name="fictional", row_count=rows, primary_key="row_id",
        fields=[FieldSpec.model_validate(field) for field in fields],
    )])
    started = time.perf_counter()
    data = generate_dataset(spec, seed=42)
    generated = time.perf_counter()
    csv = rows_to_csv(data["fictional"])
    serialized = time.perf_counter()
    if len(data["fictional"]) != rows:
        raise RuntimeError("generation lost rows")
    digest = hashlib.sha256(csv.encode()).hexdigest()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "generation_validation_seconds": generated - started,
        "csv_serialization_seconds": serialized - generated,
        "total_seconds": serialized - started,
        "peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024,
        "csv_sha256": digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--candidate-source", type=Path, default=Path("src"))
    parser.add_argument("--rows", nargs="+", type=int, default=[10_000, 100_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("generation-check.json"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if min(*args.rows, args.repeats) < 1:
        parser.error("rows and repeats must be positive")
    if args.worker:
        print(json.dumps(worker(args.baseline_source, args.rows[0])))
        return 0
    sources = {"baseline": args.baseline_source, "prepared": args.candidate_source}
    for source in sources.values():
        if not (source / "test_data_agent" / "generation" / "entity_generator.py").is_file():
            parser.error("source must contain the test_data_agent package")
    report: dict[str, Any] = {
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "dependencies": {package: version(package) for package in ("pydantic", "Faker")}},
        "settings": {"seed": 42, "columns": 25, "repeats": args.repeats,
                     "sources": {key: str(value.resolve()) for key, value in sources.items()},
                     "source_sha256": {key: {
                         path: hashlib.sha256((value / "test_data_agent" / path).read_bytes()).hexdigest()
                         for path in ("generation/entity_generator.py", "validation/schema_validator.py")
                     } for key, value in sources.items()}},
        "runs": [],
    }
    for rows in args.rows:
        expected = None
        for repeat in range(args.repeats):
            for backend in (("baseline", "prepared") if repeat % 2 == 0
                            else ("prepared", "baseline")):
                started = time.perf_counter()
                completed = subprocess.run([
                    sys.executable, str(Path(__file__).resolve()), "--worker",
                    "--baseline-source", str(sources[backend].resolve()), "--rows", str(rows),
                ], capture_output=True, text=True, check=True, timeout=360)
                result = json.loads(completed.stdout)
                if expected is None:
                    expected = result["csv_sha256"]
                if result["csv_sha256"] != expected:
                    raise RuntimeError("seeded CSV output differs between source versions")
                result.update(rows=rows, backend=backend, repeat=repeat + 1,
                              worker_wall_seconds=time.perf_counter() - started)
                report["runs"].append(result)
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                print(f"{rows}x25 {backend} #{repeat + 1}: "
                      f"{result['total_seconds']:.2f}s, "
                      f"RSS {result['peak_rss_bytes'] / 1024**2:.1f} MiB; CSV equal", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
