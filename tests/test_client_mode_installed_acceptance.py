"""Fictional installed-CLI mode/ratio acceptance, without private inputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("selection", ["explicit", "omitted"])
def test_explicit_negative_mode_reaches_installed_generation(
    tmp_path: Path, selection: str,
) -> None:
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

    spec = {
        "entities": [{"name": "fictional_orders", "row_count": 12, "fields": [
            {"name": "amount", "data_type": "integer"},
        ]}],
        "generation_settings": {"seed": 31,
                                "mode": "valid" if selection == "explicit" else "negative",
                                "invalid_ratio": 0 if selection == "explicit" else 1,
                                "output_format": "json"},
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    overrides = ["--mode", "negative", "--invalid-ratio", "1"] if selection == "explicit" else []
    completed = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "generate", "spec.json",
         *overrides, "--output", "out"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 1
    rows = json.loads((tmp_path / "out/fictional_orders.json").read_text())
    manifest = json.loads((tmp_path / "out/generation_manifest.json").read_text())
    report = json.loads((tmp_path / "out/validation_report.json").read_text())
    assert len(rows) == 12
    assert all(isinstance(row["amount"], str) for row in rows)
    assert manifest["effective_rules"]["generation_mode"] == "negative"
    assert manifest["effective_rules"]["invalid_ratio"] == 1
    assert report["valid"] is False
    assert json.loads((tmp_path / "spec.json").read_text()) == spec


@pytest.mark.parametrize("input_kind", ["spec", "profile", "csv"])
@pytest.mark.parametrize("selection", ["mixed", "default"])
def test_fractional_mixed_mode_replays_across_installed_cli_inputs(
    tmp_path: Path, input_kind: str, selection: str,
) -> None:
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
    source = tmp_path / "fictional.csv"
    source.write_text("reference,amount\nalpha,10\nbeta,20\n", encoding="utf-8")
    spec = {
        "entities": [{"name": "fictional_orders", "row_count": 200, "fields": [
            {"name": "amount", "data_type": "integer"},
        ]}],
        "generation_settings": {"seed": 31, "mode": "valid", "invalid_ratio": 0,
                                "output_format": "json"},
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    if input_kind == "profile":
        profiled = subprocess.run(
            [sys.executable, "-m", "test_data_agent.cli", "profile-csv", str(source),
             "--table", "fictional_orders", "--output", "profile.json"],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
        )
        assert profiled.returncode == 0, profiled.stderr

    rows_by_run = []
    overrides = ["--mode", "mixed", "--invalid-ratio", "0.25"] if selection == "mixed" else []
    for run in ("first", "second"):
        output = tmp_path / run
        if input_kind == "spec":
            command = ["generate", "spec.json", *overrides,
                       "--seed", "31", "--output", str(output)]
            rows_path = output / "fictional_orders.json"
            artifact_dir = output
        elif input_kind == "profile":
            rows_path = output / "fictional_orders.json"
            command = ["generate", "--profile", "profile.json", "--count", "200",
                       *overrides, "--seed", "31",
                       "--format", "json", "--output", str(rows_path)]
            artifact_dir = output
        else:
            rows_path = output / "fictional_orders.json"
            command = ["generate-from-csv", str(source), "--table", "fictional_orders",
                       "--count", "200", *overrides,
                       "--seed", "31", "--format", "json", "--output", str(rows_path)]
            artifact_dir = output
        completed = subprocess.run(
            [sys.executable, "-m", "test_data_agent.cli", *command, "--json"],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
        )
        # Owner-confirmed parity: publication survives deliberate invalidity,
        # but the exit/envelope honestly report failed validation.
        assert completed.returncode == (1 if selection == "mixed" else 0), completed.stderr
        response = json.loads(completed.stdout)
        assert response["exit_code"] == completed.returncode
        assert response["status"] == ("validation_failed" if selection == "mixed" else "succeeded")
        rows = json.loads(rows_path.read_text())
        manifest = json.loads((artifact_dir / "generation_manifest.json").read_text())
        report = json.loads((artifact_dir / "validation_report.json").read_text())
        assert len(rows) == 200
        assert manifest["effective_rules"]["generation_mode"] == ("mixed" if selection == "mixed" else "valid")
        assert manifest["effective_rules"]["invalid_ratio"] == (0.25 if selection == "mixed" else 0)
        assert report["valid"] is (selection == "default")
        invalid = sum(row["amount"] == "not-a-number" for row in rows)
        assert 0 < invalid < len(rows) if selection == "mixed" else invalid == 0
        assert all(type(row["amount"]) is int or row["amount"] == "not-a-number" for row in rows)
        rows_by_run.append(rows)
    assert rows_by_run[0] == rows_by_run[1]
    assert json.loads((tmp_path / "spec.json").read_text()) == spec
