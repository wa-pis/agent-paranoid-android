"""Bind generation-only source snapshots without running a heavy benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import benchmark_generation_dispatch as dispatch


def _source(root: Path, generation: str) -> None:
    for name, text in {
        dispatch.GENERATOR: generation,
        "src/test_data_agent/__init__.py": "# synthetic package\n",
        dispatch.paired.WRITER: "# synthetic unchanged writer\n",
        **{name: "# synthetic unchanged helper\n" for name in dispatch.paired.HELPERS},
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    cache = root / "src/test_data_agent/__pycache__"
    cache.mkdir()
    (cache / "ignored.pyc").write_bytes(b"synthetic cache")


@pytest.mark.parametrize("extra_change", [False, True])
def test_snapshots_preserve_supplied_source_and_allow_only_generator_changes(
    tmp_path, monkeypatch, extra_change,
) -> None:
    before, after = tmp_path / "input", tmp_path / "current"
    _source(before, "# synthetic original generator\n")
    _source(after, "# synthetic prepared generator\n")
    original = dispatch.paired.fingerprints(before)
    monkeypatch.setattr(dispatch, "ROOT", after)
    if extra_change:
        (after / dispatch.paired.WRITER).write_text("# synthetic unrelated change\n")
        with pytest.raises(AssertionError):
            dispatch.snapshots(tmp_path / "snapshots", before)
    else:
        paths, hashes = dispatch.snapshots(tmp_path / "snapshots", before)
        assert hashes["before"] == original
        assert hashes["after"] == dispatch.paired.fingerprints(after)
        assert paths["before"] != before
        assert not any(path.name == "__pycache__" or path.suffix == ".pyc"
                       for path in (tmp_path / "snapshots").rglob("*"))
    assert dispatch.paired.fingerprints(before) == original
    assert (before / "src/test_data_agent/__pycache__/ignored.pyc").exists()


@pytest.mark.parametrize("problem", [
    None, "helper", "writer", "csv", "snapshot", "smoke",
    "reference_relative", "reference_absolute",
])
def test_main_binds_history_retains_failures_and_preserves_before_input(
    tmp_path, monkeypatch, capsys, problem,
) -> None:
    before, after = tmp_path / "input", tmp_path / "current"
    _source(before, "# synthetic original generator\n")
    _source(after, "# synthetic prepared generator\n")
    original = dispatch.paired.fingerprints(before)
    monkeypatch.setattr(dispatch, "ROOT", after)
    monkeypatch.setattr(dispatch, "version", lambda name: "synthetic-version")
    explicit_reference = problem in {"reference_relative", "reference_absolute"}
    reference_name = (Path("openspec/changes/synthetic-generation/paired-results.json")
                      if explicit_reference else Path(dispatch.REFERENCE))
    reference_path = after / reference_name
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_text(json.dumps({
        "completed": True, "source_sha256": {"after": original},
        "environment": {"dependencies": {name: "synthetic-version" for name in
                                         ("agent-paranoid-android", "Faker", "pydantic", "PyYAML")}},
        "runs": [{"rows": 3, "mode": mode, "status": "succeeded",
                  "csv_sha256": ("a" if mode == "legacy" else "b") * 64,
                  "csv_bytes": 101} for mode in ("legacy", "streaming")],
    }))
    reference_argument = str(reference_path if problem == "reference_absolute" else reference_name)
    if explicit_reference:
        default_reference = after / dispatch.REFERENCE
        default_reference.parent.mkdir(parents=True, exist_ok=True)
        default_reference.write_text(json.dumps({"completed": False}))
    destination = tmp_path / "results.json"
    monkeypatch.setattr(dispatch.sys, "argv", [
        "benchmark_generation_dispatch.py", "--before-source", str(before),
        "--rows", "3", "--pairs", "2", "--output", str(destination),
        "--reference", reference_argument,
    ])
    monkeypatch.setattr(dispatch.paired.benchmark, "memory_sample", Mock(return_value=(100, 80, 1)))
    temporary = dispatch.tempfile.TemporaryDirectory
    monkeypatch.setattr(dispatch.tempfile, "TemporaryDirectory",
                        lambda **kwargs: temporary(dir=tmp_path, **kwargs))
    calls = []

    def measure(path: Path, rows: int, mode: str):
        calls.append(path)
        run = {
            "rows": rows, "mode": mode, "status": "succeeded", "api_seconds": 2.0,
            "sampled_peak_tree_rss_bytes": 100, "coordinator_peak_rss_bytes": 80,
            "stage_seconds": {"generation_ipc": 1.5, "csv_encoding": 0.5},
            "csv_sha256": ("a" if mode == "legacy" else "b") * 64,
            "csv_bytes": 101, "scratch_removed": True,
            "writer_sha256": dispatch.paired.benchmark.digest(path / dispatch.paired.WRITER),
        }
        if len(calls) == 12:
            if problem == "helper":
                run.update(status="failed", error_type="HelperFailure")
            elif problem == "writer":
                run["writer_sha256"] = "d" * 64
            elif problem == "csv":
                run["csv_bytes"] += 1
            elif problem == "snapshot":
                (path / dispatch.GENERATOR).write_text("# synthetic final snapshot mutation\n")
        if problem == "smoke" and len(calls) == 1:
            run.update(status="failed", error_type="HelperFailure")
        return run

    monkeypatch.setattr(dispatch.paired, "measure", measure)

    successful = problem is None or explicit_reference
    assert dispatch.main() == (0 if successful else 1)

    report = json.loads(destination.read_text())
    assert len(report["smoke_runs"]) == 4
    assert len(report["runs"]) == (0 if problem == "smoke" else 8)
    assert report["completed"] is successful
    assert report["before_source_unchanged"] and report["baseline_unchanged"]
    assert before.exists() and dispatch.paired.fingerprints(before) == original
    assert report["snapshot_scratch_removed"] and all(not path.exists() for path in calls)
    assert report["snapshots_unchanged"] is (problem != "snapshot")
    assert report["baseline"]["source_arm"] == "after"
    assert report["baseline"]["path"] == reference_argument
    assert report["source_sha256"]["before"] == original
    if problem in {"writer", "csv"}:
        assert report["runs"][-1]["status"] == "failed"
        assert report["runs"][-1]["error_type"] == "EvidenceMismatch"
    elif problem == "helper":
        assert report["runs"][-1]["error_type"] == "HelperFailure"
    elif problem == "smoke":
        assert report["smoke_runs"][0]["error_type"] == "HelperFailure"
    assert len(capsys.readouterr().out.splitlines()) == len(report["runs"])


def test_main_rejects_supplied_source_without_historical_parity(tmp_path, monkeypatch) -> None:
    before, current = tmp_path / "input", tmp_path / "current"
    _source(before, "# synthetic unexpected original\n")
    monkeypatch.setattr(dispatch, "ROOT", current)
    reference = current / dispatch.REFERENCE
    reference.parent.mkdir(parents=True)
    reference.write_text(json.dumps({"completed": True, "source_sha256": {"after": {}}}))
    monkeypatch.setattr(dispatch.sys, "argv", [
        "benchmark_generation_dispatch.py", "--before-source", str(before),
        "--output", str(tmp_path / "results.json"),
        "--reference", str(reference),
    ])
    monkeypatch.setattr(dispatch.paired.benchmark, "memory_sample", Mock(return_value=(100, 80, 1)))
    measure = Mock()
    monkeypatch.setattr(dispatch.paired, "measure", measure)

    with pytest.raises(AssertionError):
        dispatch.main()

    measure.assert_not_called()
    assert before.exists()
