"""Reviewed publication probe adaptation: fictional input, unpatched CLI.

Set TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT to an isolated installed package
directory to replay against a wheel. Otherwise test this checkout's source.
Unlike the supplied probe, successful exit and output contents are both checked.
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("state,overwrite", [
    ("absent", False), ("empty", False), ("empty", True),
    ("filled", False), ("filled", True),
])
def test_client_publication_contract(tmp_path: Path, state: str, overwrite: bool) -> None:
    package_root = Path(os.environ.get(
        "TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT",
        str(Path(__file__).resolve().parents[1] / "src"),
    )).resolve(strict=True)
    env = {**os.environ, "PYTHONPATH": str(package_root), "PYTHONDONTWRITEBYTECODE": "1"}
    probe = subprocess.run(
        [sys.executable, "-c", "import test_data_agent; print(test_data_agent.__file__)"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode == 0
    assert Path(probe.stdout.strip()).resolve().is_relative_to(package_root)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "schema_version": "1.0",
        "entities": [{"name": "deal", "row_count": 10, "fields": [
            {"name": "id", "data_type": "integer", "is_identifier": True},
            {"name": "amount", "data_type": "float"},
        ]}],
    }), encoding="utf-8")
    output = tmp_path / "output"
    if state != "absent":
        output.mkdir()
    if state == "filled":
        (output / "old.csv").write_text("id\n1\n", encoding="utf-8")
    command = [sys.executable, "-m", "test_data_agent.cli", "generate", str(spec),
               "--count", "10", "--seed", "7", "--format", "csv",
               "--output", str(output)]
    if overwrite:
        command.append("--overwrite")
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, timeout=30)
    if state == "filled":
        assert result.returncode == 2
        assert sorted(path.name for path in output.iterdir()) == ["old.csv"]
        assert (output / "old.csv").read_text(encoding="utf-8") == "id\n1\n"
    else:
        assert result.returncode == 0
        with (output / "deal.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == ["id", "amount"]
            rows = list(reader)
        assert len(rows) == 10
        assert len({row["id"] for row in rows}) == 10
        assert all(float(row["amount"]) >= 0 for row in rows)
        assert (output / "generation_manifest.json").is_file()
