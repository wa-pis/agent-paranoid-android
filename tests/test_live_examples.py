from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]


def test_csv_quickstart_runs_complete_safe_workflow(tmp_path: Path) -> None:
    output = tmp_path / "csv-quickstart"
    environment = os.environ.copy()
    installed_cli = Path(sys.executable).with_name("test-data-agent")
    assert installed_cli.is_file(), (
        "live examples must run from an installed environment with "
        "the test-data-agent entrypoint"
    )
    environment.pop("TDA_PYTHON", None)
    environment["PATH"] = os.pathsep.join(
        [str(installed_cli.parent), environment.get("PATH", "")]
    )

    subprocess.run(
        [REPOSITORY_ROOT / "examples/csv_quickstart/run.sh", output],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((output / "generated/generation_manifest.json").read_text())
    generated_validation = json.loads(
        (output / "generated/validation_report.json").read_text()
    )
    revalidation = json.loads((output / "revalidation_report.json").read_text())
    with (REPOSITORY_ROOT / "examples/csv_quickstart/customers.csv").open(
        newline=""
    ) as handle:
        source_rows = list(csv.DictReader(handle))
    with (output / "generated/customers.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert (output / "profile.json").is_file()
    assert (output / "dataset_spec.yaml").is_file()
    assert len(rows) == 25
    source_fields = tuple(source_rows[0])
    source_signatures = {
        tuple(row[field] for field in source_fields) for row in source_rows
    }
    assert all(
        tuple(row[field] for field in source_fields) not in source_signatures
        for row in rows
    )
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 12345
    assert manifest["validation_valid"] is True
    assert generated_validation["valid"] is True
    assert revalidation["valid"] is True
