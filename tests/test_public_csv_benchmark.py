from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import benchmark_public_csv as benchmark
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.workflows import generate_dataset_bundle


def test_nested_phases_measure_exclusive_time_and_restore_after_failure() -> None:
    now = [0.0]
    phases = benchmark.Phases(lambda: now[0])
    now[0] = 2
    with phases.scope("generation"):
        now[0] = 5
        with pytest.raises(ValueError, match="synthetic failure"):
            with phases.scope("validation"):
                now[0] = 11
                raise ValueError("synthetic failure")
        now[0] = 13
    now[0] = 17
    phases.tick()

    assert dict(phases.seconds) == {
        "setup_and_bookkeeping": 6, "generation": 5, "validation": 6,
    }
    assert phases.stack == ["setup_and_bookkeeping"]
    assert sum(phases.seconds.values()) == 17


def test_phase_wrapper_delegates_arguments_result_and_validation_row_counts() -> None:
    phases = benchmark.Phases(lambda: 0)
    data = {"fictional": [{"row_id": 1}, {"row_id": 2}]}
    original = Mock(return_value=object())

    result = phases.wrap(original, "mandatory_validation")(data, "synthetic_spec", strict=True)

    original.assert_called_once_with(data, "synthetic_spec", strict=True)
    assert result is original.return_value
    assert phases.calls["mandatory_validation"] == 1
    assert phases.checked_rows["mandatory_validation"] == 2


def test_streaming_budget_delegates_every_check_and_preserves_deadline() -> None:
    now = [0.0]
    original = GenerationBudget(1, clock=lambda: now[0])
    original.check = Mock(wraps=original.check)
    phases = benchmark.Phases(lambda: now[0])
    budget = benchmark.StreamingBudget(original, phases)
    stages = {
        "streaming CSV setup": "setup_and_bookkeeping",
        "parallel generation setup": "setup_and_bookkeeping",
        "parallel task submission": "generation_ipc",
        "parallel row generation": "generation_ipc",
        "streaming CSV validation": "global_checks",
        "streaming CSV encoding": "csv_encoding",
        "streaming CSV write": "csv_write",
        "streaming CSV final validation": "csv_write",
    }
    for stage, expected in stages.items():
        budget.check(stage)
        original.check.assert_called_with(stage)
        assert phases.stack[-1] == expected
    assert original.check.call_count == len(stages)
    assert budget.max_seconds == original.max_seconds == 1

    now[0] = 2
    with pytest.raises(GenerationLimitError, match="second budget"):
        budget.check("streaming CSV validation")
    original.check.assert_called_with("streaming CSV validation")
    assert phases.stack[-1] == "csv_write"


@pytest.fixture
def legacy_output(tmp_path: Path) -> tuple[Path, dict]:
    output = tmp_path / "instrumented"
    metrics = benchmark.worker(4, "legacy", output)
    return output, metrics


def test_legacy_instrumentation_preserves_public_bundle_and_checks(
    tmp_path: Path, legacy_output: tuple[Path, dict],
) -> None:
    instrumented, metrics = legacy_output
    baseline = tmp_path / "baseline"
    result = generate_dataset_bundle(
        benchmark.fictional_spec(4), output_folder=baseline,
        output_format=OutputFormat.CSV, seed=42,
    )

    assert result.validation.valid and result.synthetic and not result.source_rows_copied
    assert {path.name for path in instrumented.iterdir()} == {
        path.name for path in baseline.iterdir()
    }
    for path in baseline.iterdir():
        assert (instrumented / path.name).read_bytes() == path.read_bytes()
        assert benchmark.digest(instrumented / path.name) == benchmark.digest(path)
    assert metrics["calls"]["mandatory_validation"] == 0
    assert metrics["calls"]["report_validation"] == 0
    for name in ("combined_validation", "schema_validation", "privacy_validation",
                 "relationship_validation", "constraint_validation", "normalization"):
        assert metrics["checked_rows"][name] == 4 and metrics["calls"][name] == 1
    assert sum(metrics["stage_seconds"].values()) == pytest.approx(metrics["api_seconds"])
    assert benchmark.audit(instrumented, 4, "legacy")["manifest_and_output_hashes_valid"]


def test_streaming_worker_retains_checks_and_publishes_auditable_bundle(tmp_path: Path) -> None:
    output = tmp_path / "streaming"

    metrics = benchmark.worker(3, "streaming", output)

    assert metrics["calls"]["mandatory_validation"] == 0
    assert metrics["calls"]["report_validation"] == 0
    for name in ("combined_validation", "schema_validation", "privacy_validation",
                 "relationship_validation", "constraint_validation", "normalization"):
        assert metrics["checked_rows"][name] == 3 and metrics["calls"][name] == 1
    assert metrics["policy"]["workers"] == 4
    assert sum(metrics["stage_seconds"].values()) == pytest.approx(metrics["api_seconds"])
    audited = benchmark.audit(output, 3, "streaming")
    assert audited["engine"] == "tiled-v1"
    assert audited["exact_header_count_ordered_unique_keys"]
    assert audited["private_output"]


@pytest.mark.parametrize("tamper", [
    "row_count", "csv_hash", "manifest_flags", "manifest_hashes",
    "empty_manifest_hashes", "report", "folder_permissions", "file_permissions",
])
def test_audit_rejects_tampered_bundle(
    legacy_output: tuple[Path, dict], tamper: str,
) -> None:
    output, _ = legacy_output
    csv_path = output / "fictional.csv"
    manifest_path = output / "generation_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if tamper == "row_count":
        csv_path.write_text("\n".join(csv_path.read_text().splitlines()[:-1]) + "\n")
    elif tamper == "csv_hash":
        csv_path.write_text(csv_path.read_text().replace("synthetic_", "synthetic_changed_", 1))
    elif tamper.startswith("manifest") or tamper == "empty_manifest_hashes":
        if tamper == "manifest_flags":
            manifest["source_rows_copied"] = True
        elif tamper == "manifest_hashes":
            manifest["reproducibility"]["output_sha256"]["fictional.csv"] = "0" * 64
        else:
            manifest["reproducibility"]["output_sha256"] = {}
        manifest_path.write_text(json.dumps(manifest))
    elif tamper == "report":
        path = output / "validation_report.json"
        report = json.loads(path.read_text())
        report["valid"] = False
        path.write_text(json.dumps(report))
    elif tamper == "folder_permissions":
        output.chmod(0o755)
    else:
        csv_path.chmod(0o644)

    with pytest.raises(AssertionError):
        benchmark.audit(output, 4, "legacy")


def test_summary_flags_mismatched_repeats_and_retains_failures() -> None:
    valid = {
        "rows": 3, "mode": "legacy", "status": "succeeded", "api_seconds": 2,
        "sampled_peak_tree_rss_bytes": 100, "coordinator_peak_rss_bytes": 80,
        "stage_seconds": {"generation_ipc": 1}, "csv_sha256": "a" * 64,
    }
    changed = {**valid, "api_seconds": 4, "csv_sha256": "b" * 64}
    failed = {"rows": 3, "mode": "legacy", "status": "failed", "error_type": "RuntimeError"}

    summary, = benchmark.summarize([valid, changed, failed])

    assert summary["attempts"] == 3 and summary["failures"] == 1
    assert summary["repeat_csv_identical"] is False
    assert summary["median_api_seconds"] == 3
    assert summary["api_seconds_range"] == [2, 4]


@pytest.mark.parametrize("problem", ["hash_mismatch", "worker_failure"])
def test_main_retains_all_attempts_and_refuses_incomplete_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str,
) -> None:
    path = tmp_path / "results.json"
    runs = [{
        "rows": 3, "mode": mode, "status": "succeeded", "api_seconds": 1,
        "sampled_peak_tree_rss_bytes": 100, "coordinator_peak_rss_bytes": 80,
        "stage_seconds": {"generation_ipc": 1}, "csv_sha256": "a" * 64,
        "scratch_removed": True,
    } for mode in ("legacy", "streaming", "streaming", "legacy")]
    if problem == "hash_mismatch":
        runs[-1]["csv_sha256"] = "b" * 64
    else:
        runs[-1].update(status="failed", error_type="RuntimeError")
    monkeypatch.setattr(benchmark.sys, "argv", [
        "benchmark_public_csv.py", "--rows", "3", "--repeats", "2", "--output", str(path),
    ])
    monkeypatch.setattr(benchmark, "memory_sample", Mock(return_value=(100, 80, 1)))
    monkeypatch.setattr(benchmark, "measure", Mock(side_effect=runs))

    assert benchmark.main() == 1

    report = json.loads(path.read_text())
    assert report["completed"] is False
    assert len(report["runs"]) == 4
    assert report["runs"][-1]["csv_sha256"] == runs[-1]["csv_sha256"]
    if problem == "worker_failure":
        assert report["runs"][-1]["error_type"] == "RuntimeError"
        assert sum(item["failures"] for item in report["summary"]) == 1
    else:
        assert any(item["repeat_csv_identical"] is False for item in report["summary"])


def test_failed_worker_is_retained_without_diagnostics_and_scratch_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = Mock(returncode=7)
    process.poll.return_value = 7
    process.communicate.return_value = ("", "synthetic worker diagnostic")
    stop = Mock()
    monkeypatch.setattr(benchmark.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(benchmark, "stop_group", stop)
    monkeypatch.setattr(benchmark.tempfile, "tempdir", str(tmp_path))

    result = benchmark.measure(3, "legacy")

    assert result["status"] == "failed" and result["error_type"] == "RuntimeError"
    assert result["returncode"] == 7 and result["stderr_present"]
    assert result["scratch_removed"] and not list(tmp_path.iterdir())
    assert "synthetic worker diagnostic" not in json.dumps(result)
    stop.assert_called_once_with(process)


def test_main_rejects_csv_bytes_different_from_preoptimization_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    references = {mode: {
        "rows": 100_000, "mode": mode, "status": "succeeded",
        "csv_sha256": ("a" if mode == "legacy" else "b") * 64, "csv_bytes": 101,
        "sampled_peak_tree_rss_bytes": 100, "coordinator_peak_rss_bytes": 80,
    } for mode in ("legacy", "streaming")}
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({
        "completed": True, "runs": list(references.values()),
        "environment": {"dependencies": {}},
    }))
    runs = [{
        **references[mode], "api_seconds": 1, "stage_seconds": {"combined_validation": 1},
        "scratch_removed": True,
    } for mode in ("legacy", "streaming")]
    runs[0]["csv_bytes"] += 1
    destination = tmp_path / "results.json"
    monkeypatch.setattr(benchmark.sys, "argv", [
        "benchmark_public_csv.py", "--rows", "100000", "--repeats", "1", "--output", str(destination),
        "--reference", str(baseline_path),
    ])
    monkeypatch.setattr(benchmark, "memory_sample", Mock(return_value=(100, 80, 1)))
    monkeypatch.setattr(benchmark, "measure", Mock(side_effect=runs))

    assert benchmark.main() == 1
    report = json.loads(destination.read_text())
    assert not report["completed"]
    assert report["runs"][0]["error_type"] == "BaselineMismatch"
    assert report["runs"][0]["baseline_csv_identical"] is False
    assert report["runs"][1]["baseline_csv_identical"] is True
