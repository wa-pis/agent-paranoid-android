from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("TEST_POSTGRES_INTEGRATION") != "1",
        reason="set TEST_POSTGRES_INTEGRATION=1 for disposable PostgreSQL",
    ),
]

ROOT = Path(__file__).parents[2]


def test_postgres_query_example_runs_from_installed_package(tmp_path: Path) -> None:
    output = tmp_path / "postgres-query"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    subprocess.run(
        [ROOT / "examples/local_postgres/run-query.sh", output],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    profile_text = (output / "profile.json").read_text()
    profile = json.loads(profile_text)
    manifest = json.loads(
        (output / "generated/generation_manifest.json").read_text()
    )
    assert profile["source_type"] == "postgres_query"
    assert len(profile["source_fingerprint"]) == 64
    assert profile["source_policy_version"] == "1.0"
    assert "999999" not in profile_text
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 12345
