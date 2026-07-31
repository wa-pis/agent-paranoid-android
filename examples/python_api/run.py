"""Run the public Python API workflow from safe synthetic metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from test_data_agent import (
    DatasetProfile,
    generate_dataset_bundle,
    infer_dataset_spec,
    validate_dataset,
)


SEED = 314159
ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f"output already exists: {output}")

    profile = DatasetProfile.model_validate(
        json.loads((ROOT / "profile.json").read_text())
    )
    spec = infer_dataset_spec(profile, count=16)
    spec.generation_settings.seed = SEED

    output.mkdir(parents=True)
    (output / "reviewed_spec.json").write_text(
        spec.model_dump_json(indent=2) + "\n"
    )
    result = generate_dataset_bundle(
        spec,
        output_folder=output / "generated",
        seed=SEED,
    )

    rows_by_entity = {}
    for entity in spec.entities:
        exported_rows = json.loads(
            (output / "generated" / f"{entity.name}.json").read_text()
        )
        rows_by_entity[entity.name] = [
            {field.name: row[field.name] for field in entity.fields}
            for row in exported_rows
        ]
    independent_report = validate_dataset(rows_by_entity, spec)
    (output / "independent_validation_report.json").write_text(
        independent_report.model_dump_json(indent=2) + "\n"
    )
    if not result.validation.valid or not independent_report.valid:
        raise SystemExit("generated dataset failed validation")

    print(f"Python API example complete: {output}")


if __name__ == "__main__":
    main()
