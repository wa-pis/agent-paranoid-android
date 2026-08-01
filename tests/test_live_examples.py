from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]


def test_csv_quickstart_runs_complete_safe_workflow(tmp_path: Path) -> None:
    output = tmp_path / "csv-quickstart"
    environment = os.environ.copy()
    installed_cli = Path(sys.executable).with_name("test-data-agent")
    assert installed_cli.is_file(), (
        "live examples must run from an installed environment with "
        "the test-data-agent entrypoint"
    )
    environment.pop("TDA_PYTHON", None)
    environment["PATH"] = os.pathsep.join(
        [str(installed_cli.parent), environment.get("PATH", "")]
    )

    subprocess.run(
        [REPOSITORY_ROOT / "examples/csv_quickstart/run.sh", output],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((output / "generated/generation_manifest.json").read_text())
    generated_validation = json.loads(
        (output / "generated/validation_report.json").read_text()
    )
    revalidation = json.loads((output / "revalidation_report.json").read_text())
    with (REPOSITORY_ROOT / "examples/csv_quickstart/customers.csv").open(
        newline=""
    ) as handle:
        source_rows = list(csv.DictReader(handle))
    with (output / "generated/customers.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert (output / "profile.json").is_file()
    assert (output / "dataset_spec.yaml").is_file()
    assert len(rows) == 25
    source_fields = tuple(source_rows[0])
    source_signatures = {
        tuple(row[field] for field in source_fields) for row in source_rows
    }
    assert all(
        tuple(row[field] for field in source_fields) not in source_signatures
        for row in rows
    )
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 12345
    assert manifest["validation_valid"] is True
    assert generated_validation["valid"] is True
    assert revalidation["valid"] is True


def test_relational_csv_example_preserves_generated_relationships_and_rules(tmp_path: Path) -> None:
    output = tmp_path / "relational-csv"
    environment = os.environ.copy()
    installed_cli = Path(sys.executable).with_name("test-data-agent")
    assert installed_cli.is_file()
    environment.pop("TDA_PYTHON", None)
    environment["PATH"] = os.pathsep.join(
        [str(installed_cli.parent), environment.get("PATH", "")]
    )

    subprocess.run(
        [REPOSITORY_ROOT / "examples/relational_csv/run.sh", output],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads((output / "generated/generation_manifest.json").read_text())
    report = json.loads((output / "generated/business_validation_report.json").read_text())
    revalidation = json.loads((output / "revalidation_report.json").read_text())
    with (output / "generated/customers.csv").open(newline="") as handle:
        customers = list(csv.DictReader(handle))
    with (output / "generated/orders.csv").open(newline="") as handle:
        orders = list(csv.DictReader(handle))

    customer_ids = {row["customer_id"] for row in customers}
    assert len(customers) == 12
    assert len(orders) == 12
    assert {row["customer_id"] for row in orders} <= customer_ids
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert report["valid"] is True
    assert report["rule_fail_count"] == 0
    assert revalidation["valid"] is True


def test_python_api_example_is_installed_deterministic_and_valid(tmp_path: Path) -> None:
    first_output = tmp_path / "python-api-first"
    second_output = tmp_path / "python-api-second"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    script = REPOSITORY_ROOT / "examples/python_api/run.py"

    for output in (first_output, second_output):
        subprocess.run(
            [sys.executable, script, output],
            cwd=tmp_path,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

    first_rows = json.loads(
        (first_output / "generated/support_tickets.json").read_text()
    )
    second_rows = json.loads(
        (second_output / "generated/support_tickets.json").read_text()
    )
    manifest = json.loads(
        (first_output / "generated/generation_manifest.json").read_text()
    )
    generated_validation = json.loads(
        (first_output / "generated/validation_report.json").read_text()
    )
    independent_validation = json.loads(
        (first_output / "independent_validation_report.json").read_text()
    )

    assert len(first_rows) == 16
    assert first_rows == second_rows
    assert manifest["seed"] == 314159
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert generated_validation["valid"] is True
    assert independent_validation["valid"] is True


def test_output_format_example_exports_valid_synthetic_bundles(tmp_path: Path) -> None:
    output = tmp_path / "output-formats"
    environment = os.environ.copy()
    installed_cli = Path(sys.executable).with_name("test-data-agent")
    assert installed_cli.is_file()
    environment.pop("TDA_PYTHON", None)
    environment["PATH"] = os.pathsep.join(
        [str(installed_cli.parent), environment.get("PATH", "")]
    )

    subprocess.run(
        [REPOSITORY_ROOT / "examples/output_formats/run.sh", output],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    expected_files = {
        "csv": "support_tickets.csv",
        "json": "support_tickets.json",
        "sql": "support_tickets.sql",
        "parquet": "support_tickets.parquet",
    }
    for output_format, row_file in expected_files.items():
        manifest = json.loads(
            (output / output_format / "generation_manifest.json").read_text()
        )
        report = json.loads(
            (output / output_format / "validation_report.json").read_text()
        )
        assert (output / output_format / row_file).is_file()
        assert manifest["output_format"] == output_format
        assert manifest["row_counts"] == {"support_tickets": 4}
        assert manifest["source_rows_copied"] is False
        assert manifest["validation_valid"] is True
        assert report["valid"] is True

    sql = (output / "sql" / "support_tickets.sql").read_text()
    assert sql.count('INSERT INTO "support_tickets"') == 4
    assert "DROP " not in sql


def test_mcp_stdio_example_uses_installed_servers_and_rejects_unsafe_request(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "mcp-example"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    installed_bin = Path(sys.executable).parent
    environment["PATH"] = os.pathsep.join(
        [str(installed_bin), environment.get("PATH", "")]
    )

    subprocess.run(
        [sys.executable, REPOSITORY_ROOT / "examples/mcp_stdio/run.py", workspace],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads((workspace / "example_result.json").read_text())
    manifest = json.loads(
        (
            workspace
            / "agent/orders/generated/generation_manifest.json"
        ).read_text()
    )
    assert result["raw_sql_exposed"] is False
    assert result["unsafe_request_rejected"] is True
    assert result["approval_required_before_review"] is True
    assert result["row_counts"] == {"orders": 8}
    assert result["validation_valid"] is True
    assert result["synthetic"] is True
    assert result["source_rows_copied"] is False
    assert len(result["reviewed_spec_sha256"]) == 64
    assert manifest["seed"] == 161803
    assert manifest["source_rows_copied"] is False
