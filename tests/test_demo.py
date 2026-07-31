from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import test_data_agent.demo as demo_module
from test_data_agent.cli import main


def test_demo_cli_generates_repeatable_valid_offline_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    assert main(["demo", "--output", str(first)]) == 0
    assert main(["demo", "--output", str(second)]) == 0

    first_rows = (first / "customers.csv").read_text()
    second_rows = (second / "customers.csv").read_text()
    manifest = json.loads((first / "generation_manifest.json").read_text())
    report = json.loads((first / "validation_report.json").read_text())
    with (first / "customers.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert first_rows == second_rows
    assert len(rows) == demo_module.DEMO_COUNT
    assert manifest["seed"] == demo_module.DEMO_SEED
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert report["valid"] is True
    assert "ava.lee@example.test" not in first_rows
    assert "source rows copied: no" in capsys.readouterr().err


def test_demo_cli_rejects_existing_output_without_changes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "demo"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep")

    assert main(["demo", "--output", str(output)]) == 2

    assert marker.read_text() == "keep"
    assert "demo output already exists" in capsys.readouterr().err


def test_demo_workflow_removes_staged_artifacts_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "demo"

    def fail_generation(*args: object, **kwargs: object) -> None:
        staged_output = kwargs["output_path"]
        assert isinstance(staged_output, Path)
        staged_output.write_text("partial")
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(
        demo_module,
        "generate_dataset_from_csv_artifacts",
        fail_generation,
    )

    with pytest.raises(RuntimeError, match="synthetic failure"):
        demo_module.run_demo(output)

    assert not output.exists()
    assert not list(tmp_path.glob(".demo.*"))
