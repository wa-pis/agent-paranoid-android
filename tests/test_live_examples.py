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
    environment["TDA_PYTHON"] = sys.executable

    subprocess.run(
        [REPOSITORY_ROOT / "examples/csv_quickstart/run.sh", output],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((output / "generated/generation_manifest.json").read_text())
    revalidation = json.loads((output / "revalidation_report.json").read_text())
    with (output / "generated/customers.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert (output / "profile.json").is_file()
    assert (output / "dataset_spec.yaml").is_file()
    assert len(rows) == 25
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 12345
    assert revalidation["valid"] is True
