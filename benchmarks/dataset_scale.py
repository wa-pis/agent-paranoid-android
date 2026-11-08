"""Offline fictional throughput fixture; never reads source data."""
from __future__ import annotations
import argparse
import cProfile
import json
import os
import platform
import resource
import time
from pathlib import Path
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.io.workflows import generate_dataset_bundle


def fixture(count: int) -> DatasetSpec:
    fields = [{"name": "synthetic_key", "data_type": "integer", "is_identifier": True}]
    for index in range(24):
        kind = index % 4
        field = {"name": f"value_{index}", "data_type": ["integer", "float", "boolean", "string"][kind]}
        if kind in (0, 1):
            field["distribution"] = {"kind": "numeric", "min_value": 0, "max_value": 1000000}
        fields.append(field)
    return DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": count,
        "primary_key": "synthetic_key", "fields": fields}],
        "generation_settings": {"seed": 42, "output_format": "csv"}})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--batch-size", type=int, default=2000)
    args = parser.parse_args()
    spec = fixture(args.count)
    if args.workers is not None:
        from test_data_agent.core.execution_policy import GenerationExecutionPolicy
        spec.generation_settings.execution_policy = GenerationExecutionPolicy(workers=args.workers, batch_size=args.batch_size)
    profile = cProfile.Profile()
    started = time.monotonic()
    if args.profile:
        profile.enable()
    result = generate_dataset_bundle(spec, output_folder=args.output)
    if args.profile:
        profile.disable()
        profile.dump_stats(str(args.profile))
    print(json.dumps({"count": args.count, "columns": 25, "workers": args.workers or 1, "engine": "scalable-v1" if args.workers is not None else "legacy", "seconds": time.monotonic()-started,
        "bytes": sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file()),
        "maxrss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "maxrss_unit": "bytes" if platform.system() == "Darwin" else "KiB",
        "python": platform.python_version(), "platform": platform.platform(),
        "cpus": os.cpu_count(), "valid": result.validation.valid}))

if __name__ == '__main__':
    main()
