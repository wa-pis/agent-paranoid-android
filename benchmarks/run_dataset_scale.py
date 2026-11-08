"""Repeatable offline measurements. Run explicitly, outside normal unit tests."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--counts', nargs='+', type=int, default=[10000, 100000, 750000])
    parser.add_argument('--workers', nargs='+', type=int, default=[1, 2, 4])
    parser.add_argument('--repeat', type=int, default=3)
    baseline = parser.add_mutually_exclusive_group()
    baseline.add_argument('--baseline-root', type=Path)
    baseline.add_argument('--legacy', action='store_true')
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 5 or any(not 1 <= n <= 750000 for n in args.counts):
        parser.error('bounded benchmark: repeat 1..5, rows 1..750000')
    if any(n not in (1, 2, 4) for n in args.workers):
        parser.error('workers must be 1, 2 or 4')
    root = Path(__file__).resolve().parents[1]
    measurements = []
    for count in args.counts:
        for workers in ([None] if args.baseline_root or args.legacy else args.workers):
            for repeat in range(args.repeat):
                with tempfile.TemporaryDirectory(prefix='apa-scale-benchmark-') as folder:
                    output = Path(folder).resolve()/'generated'
                    command = [sys.executable, str(root/'benchmarks/dataset_scale.py'),
                               '--count', str(count), '--output', str(output)]
                    env = dict(os.environ)
                    if args.baseline_root or args.legacy:
                        source_root = args.baseline_root.resolve() if args.baseline_root else root
                        env.update(PYTHONPATH=str(source_root/'src'),
                            TEST_DATA_AGENT_MAX_GENERATION_COUNT='750000',
                            TEST_DATA_AGENT_MAX_OUTPUT_BYTES=str(6*1024**3),
                            TEST_DATA_AGENT_MAX_GENERATION_SECONDS='1800')
                    else:
                        command.extend(['--workers', str(workers)])
                    result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                            text=True, check=True, timeout=1800)
                    measurement = json.loads(result.stdout)
                    stats = output/'generation_statistics.json'
                    if stats.exists():
                        measurement['stages'] = json.loads(stats.read_text())
                    measurement['repeat'] = repeat
                    measurements.append(measurement)
                    args.result.write_text(json.dumps(measurements, indent=2)+'\n')
                    print(json.dumps(measurement), flush=True)


if __name__ == '__main__':
    main()
