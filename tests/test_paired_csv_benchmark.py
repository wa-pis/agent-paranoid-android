"""Pairing, provenance and failure handling without live RSS measurements."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
from unittest.mock import Mock

import pytest

from scripts import benchmark_paired_csv as paired


def _run(*, rows=3, mode="legacy", arm="before", pair=1, seconds=2.0, encoding=0.5):
    return {
        "rows": rows, "mode": mode, "arm": arm, "pair": pair, "status": "succeeded",
        "api_seconds": seconds, "sampled_peak_tree_rss_bytes": 100,
        "coordinator_peak_rss_bytes": 80, "stage_seconds": {"csv_encoding": encoding},
        "csv_sha256": ("a" if mode == "legacy" else "b") * 64,
        "csv_bytes": 101, "scratch_removed": True,
    }


def _source(root: Path, *, guards=1) -> None:
    writer = root / paired.WRITER
    writer.parent.mkdir(parents=True)
    writer.write_text("# synthetic writer\n" + paired.GUARD * guards + "# synthetic ending\n")
    (root / "src/test_data_agent/__init__.py").write_text("# synthetic package\n")
    (root / "src/test_data_agent/safety.py").write_text("# synthetic safety policy\n")
    cache = root / "src/test_data_agent/__pycache__"
    cache.mkdir()
    (cache / "ignored.pyc").write_bytes(b"synthetic cache")
    for name in paired.HELPERS:
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("# synthetic benchmark helper\n")


def test_schedule_keeps_pairs_adjacent_and_balances_abba_for_every_case() -> None:
    scheduled = list(paired.schedule([100_000, 750_000], 4))
    assert len(scheduled) == 32
    for index in range(0, len(scheduled), 2):
        left, right = scheduled[index:index + 2]
        assert left[:3] == right[:3]
        assert {left[3], right[3]} == {"before", "after"}
    for rows in (100_000, 750_000):
        for mode in ("legacy", "streaming"):
            case = [item for item in scheduled if item[:2] == (rows, mode)]
            assert [item[2] for item in case] == [1, 1, 2, 2, 3, 3, 4, 4]
            assert [item[3] for item in case] == ["before", "after", "after", "before"] * 2
        for number in range(1, 5):
            modes = [mode for count, mode, pair, _ in scheduled if count == rows and pair == number]
            assert modes == (["legacy"] * 2 + ["streaming"] * 2 if number % 2
                             else ["streaming"] * 2 + ["legacy"] * 2)


def test_snapshots_isolate_the_guard_exclude_caches_and_bind_all_helpers(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source"
    _source(source)
    original = paired.fingerprints(source)
    monkeypatch.setattr(paired, "ROOT", source)

    paths, hashes = paired.snapshots(tmp_path / "snapshots")

    assert paired.fingerprints(source) == original
    assert hashes["after"] == original
    assert set(hashes["before"]) == set(original)
    assert [name for name in original if hashes["before"][name] != original[name]] == [paired.WRITER]
    assert paired.GUARD not in (paths["before"] / paired.WRITER).read_text()
    assert (paths["after"] / paired.WRITER).read_text().count(paired.GUARD) == 1
    assert not any(path.name == "__pycache__" or path.suffix == ".pyc"
                   for path in (tmp_path / "snapshots").rglob("*"))
    helper = paths["before"] / paired.HELPERS[0]
    helper.write_text("# synthetic changed helper\n")
    assert paired.fingerprints(paths["before"]) != hashes["before"]


@pytest.mark.parametrize("guards", [0, 2])
def test_snapshots_refuse_missing_or_ambiguous_encoding_guard(tmp_path, monkeypatch, guards) -> None:
    source = tmp_path / "source"
    _source(source, guards=guards)
    monkeypatch.setattr(paired, "ROOT", source)
    with pytest.raises(AssertionError, match="exactly the measured CSV guard"):
        paired.snapshots(tmp_path / "snapshots")


def test_summary_uses_median_of_paired_changes_instead_of_ratio_of_arm_medians() -> None:
    runs = []
    for number, before in enumerate([1.0, 10.0, 100.0, 1000.0], 1):
        after = before * (2 if number < 3 else 1.1)
        encoding = before / 2
        pair = [
            _run(pair=number, arm="before", seconds=before, encoding=encoding),
            _run(pair=number, arm="after", seconds=after,
                 encoding=encoding * (0.5 if number < 3 else 0.9)),
        ]
        runs.extend(pair if number % 2 else reversed(pair))
    original = deepcopy(runs)

    summary, = paired.summarize(runs)

    assert runs == original
    assert summary["all_csv_identical"]
    assert summary["median_paired_percent_change"]["api_seconds_percent_change"] == pytest.approx(55)
    assert summary["median_paired_stage_percent_change"]["csv_encoding"] == pytest.approx(-30)
    arm_medians = {arm: statistics.median(run["api_seconds"] for run in runs if run["arm"] == arm)
                   for arm in ("before", "after")}
    assert 100 * (arm_medians["after"] / arm_medians["before"] - 1) != pytest.approx(55)
    assert [pair["order"] for pair in summary["pairs"]] == [
        ["before", "after"], ["after", "before"], ["before", "after"], ["after", "before"],
    ]
    assert summary["pairs"][0]["csv_encoding_seconds_delta"] == -0.25


def test_summary_retains_failed_and_incomplete_attempts_and_does_not_invent_pairs() -> None:
    failed = {"rows": 3, "mode": "legacy", "arm": "after", "pair": 2,
              "status": "failed", "error_type": "HelperFailure"}
    runs = [_run(), _run(arm="after"), _run(pair=2), failed, _run(pair=3)]

    summary, = paired.summarize(runs)

    assert len(summary["pairs"]) == 1 and summary["pairs"][0]["pair"] == 1
    assert summary["arms"]["before"][0]["attempts"] == 3
    assert summary["arms"]["after"][0]["attempts"] == 2
    assert summary["arms"]["after"][0]["failures"] == 1
    assert runs[3] is failed and failed["error_type"] == "HelperFailure"
    only_failure, = paired.summarize([failed])
    assert only_failure["pairs"] == [] and only_failure["all_csv_identical"] is False
    assert only_failure["median_paired_percent_change"] == {}
    assert only_failure["median_paired_stage_percent_change"] == {}


@pytest.mark.parametrize("changed", [{"csv_sha256": "c" * 64}, {"csv_bytes": 102}])
def test_summary_requires_csv_hash_and_size_equality(changed) -> None:
    summary, = paired.summarize([_run(), {**_run(arm="after"), **changed}])
    assert not summary["all_csv_identical"]


@pytest.mark.parametrize("returncode", [0, 7])
def test_measure_runs_the_unchanged_helper_in_the_selected_snapshot_without_diagnostics(
    tmp_path, monkeypatch, returncode,
) -> None:
    canary = "synthetic diagnostic that must not enter failure evidence"
    payload = _run()
    completed = subprocess.CompletedProcess([], returncode, json.dumps(payload) if not returncode else canary,
                                            canary)
    execute = Mock(return_value=completed)
    monkeypatch.setattr(paired.subprocess, "run", execute)

    result = paired.measure(tmp_path, 3, "legacy")

    args, kwargs = execute.call_args
    assert args[0] == [paired.sys.executable, "-c", paired.HELPER, str(tmp_path), "3", "legacy"]
    assert kwargs["cwd"] == tmp_path and kwargs["capture_output"] and kwargs["text"]
    assert kwargs["env"]["PYTHONPATH"] == os.pathsep.join([str(tmp_path / "src"), str(tmp_path / "scripts")])
    assert kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert kwargs["env"]["PYTHONHASHSEED"] == "0"
    if returncode:
        assert result["status"] == "failed" and result["error_type"] == "HelperFailure"
        assert result["returncode"] == 7 and result["stderr_present"]
        assert canary not in json.dumps(result)
    else:
        assert result == payload


@pytest.mark.parametrize("problem,history", [
    (None, False), (None, True), ("helper", True), ("source", True),
    ("hash", True), ("bytes", True), ("snapshot", True),
])
def test_main_retains_attempts_verifies_history_and_cleans_snapshot_scratch(
    tmp_path, monkeypatch, capsys, problem, history,
) -> None:
    source = tmp_path / "source"
    _source(source)
    monkeypatch.setattr(paired, "ROOT", source)
    monkeypatch.setattr(paired, "version", lambda name: "synthetic-version")
    hashes = paired.fingerprints(source)
    old_hashes = dict(hashes)
    old_hashes[paired.WRITER] = hashlib.sha256(
        (source / paired.WRITER).read_text().replace(paired.GUARD, "", 1).encode()
    ).hexdigest()
    for folder, snapshot in (("value-normalization-performance", old_hashes),
                             ("csv-encoding-performance", hashes)):
        path = source / "openspec/changes" / folder / "public-csv-results.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "completed": True, "source_sha256": snapshot,
            "environment": {"dependencies": {name: "synthetic-version" for name in
                                             ("agent-paranoid-android", "Faker", "pydantic", "PyYAML")}},
            "runs": [_run(mode=mode) for mode in ("legacy", "streaming")],
        }))
    destination = tmp_path / "results.json"
    monkeypatch.setattr(paired.sys, "argv", [
        "benchmark_paired_csv.py", "--rows", "3", "--pairs", "2", "--output", str(destination),
        *(["--historical-root", str(source / "openspec/changes"),
           "--reference", str(source / "openspec/changes/csv-encoding-performance/public-csv-results.json")]
          if history else []),
    ])
    monkeypatch.setattr(paired.benchmark, "memory_sample", Mock(return_value=(100, 80, 1)))
    temporary = paired.tempfile.TemporaryDirectory
    monkeypatch.setattr(paired.tempfile, "TemporaryDirectory",
                        lambda **kwargs: temporary(dir=tmp_path, **kwargs))
    calls = []

    def measure(path, rows, mode):
        calls.append((path, rows, mode))
        result = {**_run(rows=rows, mode=mode), "writer_sha256": paired.benchmark.digest(path / paired.WRITER)}
        if len(calls) == 12:
            if problem == "helper":
                result.update(status="failed", error_type="HelperFailure")
            elif problem == "source":
                result["writer_sha256"] = "d" * 64
            elif problem == "hash":
                result["csv_sha256"] = "d" * 64
            elif problem == "bytes":
                result["csv_bytes"] += 1
            elif problem == "snapshot":
                (path / paired.HELPERS[0]).write_text("# synthetic mutation after final run\n")
        return result

    monkeypatch.setattr(paired, "measure", measure)

    assert paired.main() == (0 if problem is None else 1)

    report = json.loads(destination.read_text())
    assert len(calls) == 12 and len(report["smoke_runs"]) == 4 and len(report["runs"]) == 8
    assert report["completed"] is (problem is None)
    assert report["snapshot_scratch_removed"] and all(not path.exists() for path, _, _ in calls)
    assert report["snapshots_unchanged"] is (problem != "snapshot")
    assert all(value["all_source_hashes_equal"] and value["same_dependencies"]
               for value in report["historical_sources"].values())
    assert bool(report["historical_sources"]) is history
    if problem in {"source", "hash", "bytes"}:
        assert report["runs"][-1]["status"] == "failed"
        assert report["runs"][-1]["error_type"] == "EvidenceMismatch"
    elif problem == "helper":
        assert report["runs"][-1]["error_type"] == "HelperFailure"
    assert len(capsys.readouterr().out.splitlines()) == 8


@pytest.mark.parametrize("arguments", [
    ["--rows", "0"], ["--rows", "750001"], ["--rows", "3", "3"],
    ["--pairs", "0"], ["--pairs", "1"], ["--pairs", "3"],
])
def test_main_rejects_invalid_or_unbalanced_experiments_before_measurement(tmp_path, monkeypatch, arguments):
    memory = Mock()
    monkeypatch.setattr(paired.benchmark, "memory_sample", memory)
    monkeypatch.setattr(paired.sys, "argv", [
        "benchmark_paired_csv.py", *arguments, "--output", str(tmp_path / "results.json"),
    ])
    with pytest.raises(SystemExit) as caught:
        paired.main()
    assert caught.value.code == 2
    memory.assert_not_called()
