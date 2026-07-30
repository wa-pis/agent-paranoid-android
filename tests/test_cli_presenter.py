from __future__ import annotations

import json
from pathlib import Path

from test_data_agent.cli_presenter import write_validation_result
from test_data_agent.validation import DatasetValidationReport


def validation_report(*, valid: bool) -> DatasetValidationReport:
    return DatasetValidationReport.model_validate(
        {
            "valid": valid,
            "sections": [
                {
                    "name": "schema",
                    "passed": 2 if valid else 1,
                    "failed": 0 if valid else 1,
                    "errors": [] if valid else ["synthetic validation failure"],
                }
            ],
        }
    )


def test_validation_result_writes_json_and_failure_exit_code(capsys) -> None:
    exit_code = write_validation_result(validation_report(valid=False), None)

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.err == "Validation failed: 1 checks passed, 1 failed.\n"
    assert json.loads(captured.out)["valid"] is False


def test_validation_result_with_output_path_suppresses_stdout(capsys) -> None:
    exit_code = write_validation_result(
        validation_report(valid=True),
        Path("validation_report.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err.endswith(" Report: validation_report.json\n")
