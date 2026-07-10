"""Run the safe Trino-profile to synthetic-dataset demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io import generate_dataset_bundle, infer_dataset_spec_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=Path("examples/trino_safe_profile.json"))
    parser.add_argument("--output", type=Path, default=Path("out/ai_demo"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=12345)
    args = parser.parse_args()

    loaded = load_profile_or_spec(args.profile)
    if isinstance(loaded, DatasetSpec):
        raise SystemExit("--profile expects safe profile metadata, not a DatasetSpec")

    spec_path = args.output / "dataset_spec.yaml"
    spec = infer_dataset_spec_artifact(loaded, output_path=spec_path, count=args.count)
    result = generate_dataset_bundle(
        spec,
        output_folder=args.output,
        output_format=OutputFormat.CSV,
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "profile": str(args.profile),
                "spec": str(spec_path),
                "output": str(args.output),
                **result.model_dump(mode="json"),
            },
            indent=2,
        )
    )
    return 0 if result.validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
