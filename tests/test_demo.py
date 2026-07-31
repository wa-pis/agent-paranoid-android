from __future__ import annotations

import csv
import hashlib
import json
import socket
from pathlib import Path

import pytest

import test_data_agent.demo as demo_module
from test_data_agent.cli import main
from test_data_agent.io import GenerationManifest, validate_dataset_artifacts
from test_data_agent.validation import DatasetValidationReport


def test_demo_cli_generates_repeatable_valid_offline_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline demo attempted network access")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    first = tmp_path / "first"
    second = tmp_path / "second"

    assert main(["demo", "--output", str(first)]) == 0
    assert main(["demo", "--output", str(second)]) == 0

    first_rows = (first / "customers.csv").read_text()
    second_rows = (second / "customers.csv").read_text()
    manifest = json.loads((first / "generation_manifest.json").read_text())
    report = json.loads((first / "validation_report.json").read_text())
    typed_manifest = GenerationManifest.model_validate(manifest)
    typed_report = DatasetValidationReport.model_validate(report)
    independent_report = validate_dataset_artifacts(
        first / "dataset_spec.json",
        first,
    )
    with (first / "customers.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert first_rows == second_rows
    assert len(rows) == demo_module.DEMO_COUNT
    assert manifest["seed"] == demo_module.DEMO_SEED
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert report["valid"] is True
    assert typed_report.valid is True
    assert independent_report.valid is True
    assert typed_manifest.reproducibility is not None
    assert typed_manifest.reproducibility.output_sha256["customers.csv"] == (
        hashlib.sha256((first / "customers.csv").read_bytes()).hexdigest()
    )
    assert "ava.lee@example.test" not in first_rows
    assert "source rows copied: no" in capsys.readouterr().err


def test_demo_rejects_missing_installed_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(demo_module, "files", lambda package: tmp_path / "missing")

    with pytest.raises(ValueError, match="installed demo fixture is missing"):
        demo_module.run_demo(tmp_path / "demo")

    assert not (tmp_path / "demo").exists()


def test_demo_propagates_unwritable_output_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "demo"

    def reject_output(path: Path) -> Path:
        raise PermissionError(f"permission denied: {path}")

    monkeypatch.setattr(demo_module, "make_temp_output_folder", reject_output)

    with pytest.raises(PermissionError, match="permission denied"):
        demo_module.run_demo(output)

    assert not output.exists()


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
