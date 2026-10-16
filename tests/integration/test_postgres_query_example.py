from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
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


@pytest.mark.parametrize(
    ("launcher", "source_type"),
    [
        ("run.sh", "postgres"),
        ("run-jdbc.sh", "postgres"),
        ("run-wildcard.sh", "postgres"),
        ("run-query.sh", "postgres_query"),
    ],
)
def test_postgres_examples_run_from_installed_package(
    tmp_path: Path,
    launcher: str,
    source_type: str,
) -> None:
    output = tmp_path / launcher.removesuffix(".sh")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    # Packaged Linux defaults can point at a system-owned socket directory.
    # Force that condition everywhere; the example must use its TCP endpoint.
    initdb = shutil.which("initdb")
    assert initdb is not None
    commands = tmp_path / "commands"
    commands.mkdir()
    shim = commands / "initdb"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, subprocess, sys\n"
        f"subprocess.run([{initdb!r}, *sys.argv[1:]], check=True)\n"
        "data = pathlib.Path(sys.argv[sys.argv.index('-D') + 1])\n"
        "with (data / 'postgresql.conf').open('a') as config:\n"
        " config.write(\"\\nunix_socket_directories = '/apa-unavailable-socket-directory'\\n\")\n"
    )
    shim.chmod(0o755)
    environment["PATH"] = str(commands) + os.pathsep + environment["PATH"]

    completed = subprocess.run(
        [ROOT / f"examples/local_postgres/{launcher}", output],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        marker = re.search(
            r"APA_POSTGRES_EXAMPLE_FAILURE stage=([a-z_]+)", completed.stderr
        )
        stage = marker.group(1) if marker else "unknown"
        pytest.fail(
            f"{launcher} failed: exit={completed.returncode}, stage={stage}",
            pytrace=False,
        )

    profile_text = (output / "profile.json").read_text()
    profile = json.loads(profile_text)
    manifest = json.loads(
        (output / "generated/generation_manifest.json").read_text()
    )
    assert profile["source_type"] == source_type
    if source_type == "postgres_query":
        assert len(profile["source_fingerprint"]) == 64
        assert profile["source_policy_version"] == "1.1"
        assert "999999" not in profile_text
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 12345
