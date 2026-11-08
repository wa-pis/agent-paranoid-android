"""Offline fictional throughput fixture; never reads source data."""
from __future__ import annotations
import argparse
import cProfile
import json
import hashlib
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


def relational_fixture(count: int) -> DatasetSpec:
    if count < 5:
        raise ValueError('linked benchmark requires at least five total rows')
    base = fixture(count)
    entities = []
    relationships = []
    counts = [count//5, count*2//5, count-count//5-count*2//5]
    for index, name in enumerate(['accounts', 'purchases', 'items']):
        entity = base.entities[0].model_copy(deep=True)
        entity.name = name
        entity.row_count = counts[index]
        if index:
            entity.fields[1].name = 'parent_key'
            relationships.append(dict(parent_entity=entities[-1].name, parent_field='synthetic_key',
                child_entity=name, child_field='parent_key', confidence=1))
        entities.append(entity)
    return DatasetSpec.model_validate(dict(entities=[e.model_dump() for e in entities], relationships=relationships,
        generation_settings=base.generation_settings.model_dump()))


def data_hashes(folder: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(folder.glob('*.csv')):
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024*1024), b''):
                digest.update(block)
        hashes[path.name] = digest.hexdigest()
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument('--relational', action='store_true')
    args = parser.parse_args()
    spec = relational_fixture(args.count) if args.relational else fixture(args.count)
    if args.relational and args.workers is None:
        parser.error('relational measurements require --workers')
    if args.workers is not None:
        from test_data_agent.core.execution_policy import GenerationExecutionPolicy
        spec.generation_settings.execution_policy = GenerationExecutionPolicy(engine='scalable-relational-v1' if args.relational else 'scalable-v1', workers=args.workers, batch_size=args.batch_size)
    profile = cProfile.Profile()
    started = time.monotonic()
    if args.profile:
        profile.enable()
    result = generate_dataset_bundle(spec, output_folder=args.output)
    if args.profile:
        profile.disable()
        profile.dump_stats(str(args.profile))
    print(json.dumps({"count": args.count, "columns": 25, "workers": args.workers or 1, "engine": spec.generation_settings.execution_policy.engine if args.workers is not None else "legacy", "data_sha256": data_hashes(args.output), "seconds": time.monotonic()-started,
        "bytes": sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file()),
        "maxrss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "maxrss_unit": "bytes" if platform.system() == "Darwin" else "KiB",
        "python": platform.python_version(), "platform": platform.platform(),
        "cpus": os.cpu_count(), "valid": result.validation.valid}))

if __name__ == '__main__':
    main()
