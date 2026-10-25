"""The acceptance ledger must not inflate coverage or escape its wheel env."""
from __future__ import annotations

import json
from pathlib import Path
from decimal import Decimal
import sys
import subprocess
from typing import Any
import pytest

from scripts import accept_cross_interface_matrix as campaign


def arguments(tmp_path: Path, *extra: str) -> Any:
    return campaign.parser().parse_args([
        "--package-root", str(tmp_path), "--sha", "a" * 40,
        "--output", str(tmp_path / "evidence.json"), *extra,
    ])


def test_expected_ledger_contains_every_logical_cell_once(tmp_path: Path) -> None:
    cases = campaign.ledger(arguments(tmp_path))
    assert len(cases) == 600
    assert len({case["id"] for case in cases}) == 600
    assert {case["status"] for case in cases} == {"blocked"}
    assert {case["reason"] for case in cases} == {"not_executed"}
    subset = campaign.ledger(arguments(tmp_path, "--source", "csv",
                                      "--output-format", "json", "--mode", "negative"))
    assert len(subset) == 3


def test_typed_fingerprints_do_not_conflate_values() -> None:
    cases = [None, "", 1, "1", True, Decimal("1.00"), Decimal("1.0")]
    assert len({campaign.digest({"value": value}) for value in cases}) == len(cases)


def test_process_environment_excludes_credentials_and_import_paths(monkeypatch: Any,
                                                                  tmp_path: Path) -> None:
    for key in ("PYTHONPATH", "OPENAI_API_KEY", "TRINO_PASSWORD", "POSTGRES_PASSWORD",
                "TEST_DATA_AGENT_AUDIT_LOG"):
        monkeypatch.setenv(key, "fictional-private-marker")
    environment = campaign.clean_environment(tmp_path)
    assert "fictional-private-marker" not in environment.values()
    assert environment["TEST_DATA_AGENT_WORKSPACE_ROOT"] == str(tmp_path)
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"


def test_controller_preserves_virtualenv_interpreter_symlink(monkeypatch: Any,
                                                            tmp_path: Path) -> None:
    python = tmp_path / "venv-python"
    python.symlink_to(sys.executable)
    output = tmp_path / "evidence.json"
    captured: list[str] = []

    def complete(command: list[str], workspace: Path, timeout: float) -> tuple[bool, int]:
        captured.extend(command)
        assert workspace != Path.cwd()
        assert timeout > 0
        report = json.loads(output.read_text())
        for case in report["cases"]:
            case["status"] = "passed"
        report.update(worker_complete=True, mcp_teardown="process_reaped")
        campaign.save_report(output, report)
        return False, 0

    monkeypatch.setattr(campaign, "supervise", complete)
    monkeypatch.setattr(sys, "argv", ["accept-matrix", "--python", str(python),
        "--package-root", str(tmp_path), "--sha", "a" * 40, "--output", str(output),
        "--source", "csv", "--output-format", "json", "--mode", "valid"])
    assert campaign.main() == 0
    assert captured[0] == str(python)
    assert captured[0] != str(python.resolve())
    assert json.loads(output.read_text())["is_full_logical_matrix"] is False


@pytest.mark.parametrize(("returncode", "completed", "teardown", "reason"), [
    (1, True, "process_reaped", "worker_exit_failed"),
    (0, False, "process_reaped", "worker_completion_missing"),
    (0, True, None, "mcp_teardown_missing"),
])
def test_all_passed_cells_cannot_hide_incomplete_worker(
    monkeypatch: Any, tmp_path: Path, returncode: int, completed: bool,
    teardown: str | None, reason: str,
) -> None:
    output = tmp_path / "evidence.json"

    def crash(command: list[str], workspace: Path, timeout: float) -> tuple[bool, int]:
        report = json.loads(output.read_text())
        for case in report["cases"]:
            case["status"] = "passed"
        report.update(worker_complete=completed, mcp_teardown=teardown)
        campaign.save_report(output, report)
        return False, returncode

    monkeypatch.setattr(campaign, "supervise", crash)
    monkeypatch.setattr(sys, "argv", ["accept-matrix", "--package-root", str(tmp_path),
        "--sha", "a" * 40, "--output", str(output), "--source", "csv", "--mode", "valid"])
    assert campaign.main() == 1
    assert json.loads(output.read_text())["campaign_error"] == reason


def test_evidence_counts_preserve_unexecuted_cells(tmp_path: Path) -> None:
    output = tmp_path / "evidence.json"
    report = {"cases": campaign.ledger(arguments(tmp_path, "--source", "csv",
              "--output-format", "json", "--mode", "valid"))}
    report["cases"][0].update(status="failed", reason="fixed_failure_category")
    campaign.save_report(output, report)
    persisted = json.loads(output.read_text())
    assert persisted["counts"] == {"failed": 1, "blocked": 2}
    assert not output.with_suffix(".json.tmp").exists()


def test_isolated_fixture_loads_local_helpers_and_restores_import_path(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    support = tmp_path / "fictional_fixture_support"
    support.mkdir()
    (support / "__init__.py").write_text("answer = 42\n")
    fixture = fixtures / "matrix.py"
    fixture.write_text("from fictional_fixture_support import answer\n")
    result = subprocess.run(
        [sys.executable, "-I", "-c",
         "import runpy,sys; from pathlib import Path; "
         "module=runpy.run_path(sys.argv[1]); before=sys.path[:]; "
         "fixture=module['load_fixture'](Path(sys.argv[2])); "
         "assert fixture['answer']==42; assert sys.path==before",
         str(Path(campaign.__file__).resolve()), str(fixture)],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_fixture_failure_also_restores_import_path(tmp_path: Path) -> None:
    fixture = tmp_path / "failing.py"
    fixture.write_text("raise ValueError('fictional failure')\n")
    original_path = sys.path[:]
    with pytest.raises(ValueError, match="fictional failure"):
        campaign.load_fixture(fixture)
    assert sys.path == original_path
