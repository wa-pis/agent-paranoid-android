import csv
import json
from pathlib import Path

import pytest

import test_data_agent.cli as cli_module
from test_data_agent.cli import main


FIXTURE_CUSTOMERS = Path("tests/fixtures/customers.csv")
FIXTURE_EXAMPLE_DATASET = Path("tests/fixtures/example_dataset")


def test_cli_help_mentions_quickstart_paths(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "generate-from-csv" in captured.out
    assert "generate-from-example" in captured.out
    assert "doctor" in captured.out
    assert "generation_manifest.json" in captured.out
    assert "synthetic" in captured.out


def test_doctor_runs_quickstart_smoke_without_repository_fixture(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "python: ok" in captured.err
    assert "dependency pydantic: ok" in captured.err
    assert "quickstart smoke: ok" in captured.err
    assert "doctor passed" in captured.err


def test_doctor_can_skip_smoke(capsys) -> None:
    exit_code = main(["doctor", "--skip-smoke"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "dependency pydantic: ok" in captured.err
    assert "quickstart smoke: ok" not in captured.err
    assert "doctor passed" in captured.err


def test_doctor_allows_missing_optional_extra(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_import = cli_module.importlib.import_module

    def import_without_pyarrow(name: str):
        if name == "pyarrow":
            raise ImportError("not installed")
        return real_import(name)

    monkeypatch.setattr(cli_module.importlib, "import_module", import_without_pyarrow)

    assert main(["doctor", "--skip-smoke"]) == 0
    assert "extra parquet: not installed (optional)" in capsys.readouterr().err


def test_doctor_fails_when_required_extra_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_import = cli_module.importlib.import_module

    def import_without_pyarrow(name: str):
        if name == "pyarrow":
            raise ImportError("not installed")
        return real_import(name)

    monkeypatch.setattr(cli_module.importlib, "import_module", import_without_pyarrow)

    assert main(["doctor", "--skip-smoke", "--require-extra", "parquet"]) == 1
    captured = capsys.readouterr()
    assert "extra parquet: missing pyarrow" in captured.err
    assert "agent-paranoid-android[parquet]" in captured.err


def test_agent_plan_and_approve_cli_flow(tmp_path, capsys) -> None:
    workspace = tmp_path / "agent"

    plan_exit = main(
        [
            "agent-plan",
            str(FIXTURE_EXAMPLE_DATASET),
            "--source-type",
            "csv-folder",
            "--workspace",
            str(workspace),
            "--count",
            "3",
            "--seed",
            "42",
            "--format",
            "csv",
        ]
    )

    plan_output = capsys.readouterr()

    assert plan_exit == 0
    assert "Agent plan ready:" in plan_output.err
    assert (workspace / "dataset_spec.yaml").is_file()
    assert not (workspace / "generated").exists()

    approve_exit = main(["agent-approve", str(workspace)])

    approve_output = capsys.readouterr()
    manifest = json.loads((workspace / "generated" / "generation_manifest.json").read_text())

    assert approve_exit == 0
    assert "Agent generation completed:" in approve_output.err
    assert "source rows copied: no" in approve_output.err
    assert manifest["source_rows_copied"] is False
    assert manifest["row_counts"] == {"customers": 3, "orders": 3}


def test_quickstart_subcommand_help_mentions_artifacts(capsys) -> None:
    with pytest.raises(SystemExit) as csv_help:
        main(["generate-from-csv", "--help"])

    csv_output = capsys.readouterr().out

    with pytest.raises(SystemExit) as folder_help:
        main(["generate-from-example", "--help"])

    folder_output = capsys.readouterr().out

    assert csv_help.value.code == 0
    assert "tests/fixtures/customers.csv" in csv_output
    assert "csv_profile.json" in csv_output
    assert "generation_manifest.json" in csv_output
    assert folder_help.value.code == 0
    assert "tests/fixtures/example_dataset" in folder_output
    assert "dataset_spec.yaml" in folder_output
    assert "generation_manifest.json" in folder_output


def test_quickstart_folder_golden_path_writes_safe_artifacts(tmp_path, capsys) -> None:
    output_dir = tmp_path / "generated"

    exit_code = main(
        [
            "generate-from-example",
            str(FIXTURE_EXAMPLE_DATASET),
            "--count",
            "25",
            "--seed",
            "12345",
            "--format",
            "csv",
            "--output",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    profile_text = (output_dir / "profile.json").read_text()
    manifest = json.loads((output_dir / "generation_manifest.json").read_text())
    report = json.loads((output_dir / "validation_report.json").read_text())
    generated_rows = load_csv_folder(output_dir)
    source_rows = load_csv_folder(FIXTURE_EXAMPLE_DATASET)

    assert exit_code == 0
    assert "Generated synthetic dataset:" in captured.err
    assert "customers=25" in captured.err
    assert "orders=25" in captured.err
    assert "seed: 12345" in captured.err
    assert "source rows copied: no" in captured.err
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert manifest["seed"] == 12345
    assert manifest["output_format"] == "csv"
    assert manifest["row_counts"] == {"customers": 25, "orders": 25}
    assert report["valid"] is True
    assert "alice@example.com" not in profile_text
    assert "bob@example.com" not in profile_text
    assert not copied_rows(generated_rows, source_rows)


def test_generate_from_profile_writes_data_spec_and_report(tmp_path) -> None:
    profile_path = tmp_path / "orders_profile.json"
    output_path = tmp_path / "out" / "orders.csv"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 100},
                    {
                        "name": "status",
                        "data_type": "varchar",
                        "top_values": [{"value": "new"}, {"value": "shipped"}],
                        "approx_distinct_count": 2,
                    },
                    {
                        "name": "created_at",
                        "data_type": "timestamp",
                        "min_timestamp": "2024-01-01T00:00:00",
                        "max_timestamp": "2024-01-02T00:00:00",
                    },
                ],
            }
        )
    )

    exit_code = main(
        [
            "generate",
            "--profile",
            str(profile_path),
            "--count",
            "10",
            "--mode",
            "mixed",
            "--invalid-ratio",
            "0.25",
            "--seed",
            "12345",
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    with output_path.open() as handle:
        rows = list(csv.DictReader(handle))

    profile = json.loads((output_path.parent / "profile.json").read_text())
    spec = json.loads((output_path.parent / "dataset_spec.json").read_text())
    report = json.loads((output_path.parent / "validation_report.json").read_text())

    assert len(rows) == 10
    assert profile["source_type"] == "json_profile"
    assert spec["generation_settings"]["seed"] == 12345
    assert spec["generation_settings"]["output_format"] == "csv"
    assert spec["generation_settings"]["mode"] == "mixed"
    assert spec["generation_settings"]["invalid_ratio"] == 0.25
    assert spec["entities"][0]["row_count"] == 10
    assert report["valid"] is False
    assert sum(section["failed"] for section in report["sections"]) > 0


def test_generate_from_profile_uses_dataset_pipeline(tmp_path) -> None:
    profile_path = tmp_path / "orders_profile.json"
    output_path = tmp_path / "out" / "orders.json"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 100},
                ],
            }
        )
    )

    exit_code = main(
        [
            "generate",
            "--profile",
            str(profile_path),
            "--count",
            "2",
            "--seed",
            "3",
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0


def test_infer_spec_routes_through_dataset_command_helper(tmp_path) -> None:
    profile_path = tmp_path / "orders_profile.json"
    output_path = tmp_path / "dataset_spec.yaml"
    profile_path.write_text(
        json.dumps(
            {
                "table": "orders",
                "columns": [
                    {"name": "order_id", "data_type": "bigint", "p05": 1, "p95": 100},
                ],
            }
        )
    )

    exit_code = main(["infer-spec", str(profile_path), "--output", str(output_path), "--count", "4"])

    spec_yaml = output_path.read_text()

    assert exit_code == 0
    assert "name: orders" in spec_yaml
    assert "row_count: 4" in spec_yaml


def test_profile_csv_routes_through_dataset_command_helper(tmp_path) -> None:
    output_path = tmp_path / "profile.json"

    exit_code = main(
        [
            "profile-csv",
            str(FIXTURE_CUSTOMERS),
            "--table",
            "customers_cli",
            "--output",
            str(output_path),
        ]
    )

    payload = json.loads(output_path.read_text())

    assert exit_code == 0
    assert payload["source_type"] == "csv"
    assert payload["entities"][0]["name"] == "customers_cli"


def test_profile_example_routes_through_dataset_command_helper(tmp_path) -> None:
    output_path = tmp_path / "profile.json"

    exit_code = main(
        [
            "profile-example",
            str(FIXTURE_EXAMPLE_DATASET),
            "--output",
            str(output_path),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )

    payload = json.loads(output_path.read_text())

    assert exit_code == 0
    assert payload["source_type"] == "csv_folder"
    assert {entity["name"] for entity in payload["entities"]} == {"customers", "orders"}


def test_generate_dataset_spec_uses_embedded_seed_when_cli_seed_is_omitted(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    output_path = tmp_path / "generated"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 3
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
      - name: status
        data_type: string
        distribution:
          kind: categorical
          categories:
            - value: active
              count: 2
            - value: paused
              count: 1
generation_settings:
  seed: 17
  output_format: csv
"""
    )

    first_exit = main(["generate", str(spec_path), "--format", "csv", "--output", str(output_path)])
    first_rows = list(csv.DictReader((output_path / "customers.csv").open()))

    second_output = tmp_path / "generated_again"
    second_exit = main(["generate", str(spec_path), "--format", "csv", "--output", str(second_output)])
    second_rows = list(csv.DictReader((second_output / "customers.csv").open()))

    assert first_exit == 0
    assert second_exit == 0
    assert first_rows == second_rows
    assert [row["customer_id"] for row in first_rows] == ["17000001", "17000002", "17000003"]


def test_generate_dataset_spec_uses_embedded_output_format_when_cli_format_is_omitted(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    output_path = tmp_path / "generated"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 2
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
      - name: status
        data_type: string
generation_settings:
  seed: 7
  output_format: json
"""
    )

    exit_code = main(["generate", str(spec_path), "--output", str(output_path)])

    rows = json.loads((output_path / "customers.json").read_text())
    report = json.loads((output_path / "validation_report.json").read_text())

    assert exit_code == 0
    assert rows[0]["customer_id"] == 7000001
    assert report["valid"] is True
    assert not (output_path / "customers.csv").exists()


def test_generate_dataset_spec_uses_dataset_pipeline(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    output_path = tmp_path / "generated"
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 1
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
generation_settings:
  seed: 5
  output_format: json
"""
    )

    exit_code = main(["generate", str(spec_path), "--output", str(output_path)])

    assert exit_code == 0
    assert (output_path / "generation_manifest.json").is_file()


def test_generate_accepts_dataset_spec_json(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.json"
    output_path = tmp_path / "generated"
    spec_path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 2,
                        "primary_key": "customer_id",
                        "fields": [
                            {"name": "customer_id", "data_type": "integer", "is_identifier": True},
                            {"name": "status", "data_type": "string"},
                        ],
                    }
                ],
                "generation_settings": {"seed": 21, "output_format": "json"},
            }
        )
    )

    exit_code = main(["generate", str(spec_path), "--format", "json", "--output", str(output_path)])

    rows = json.loads((output_path / "customers.json").read_text())
    report = json.loads((output_path / "validation_report.json").read_text())

    assert exit_code == 0
    assert len(rows) == 2
    assert rows[0]["customer_id"] == 21000001
    assert report["valid"] is True


def test_validate_accepts_dataset_spec_json(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.json"
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    spec_path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 2,
                        "primary_key": "customer_id",
                        "fields": [
                            {"name": "customer_id", "data_type": "integer", "is_identifier": True},
                            {"name": "status", "data_type": "string"},
                        ],
                    }
                ]
            }
        )
    )
    (rows_dir / "customers.json").write_text(
        json.dumps(
            [
                {"customer_id": 1, "status": "active"},
                {"customer_id": 2, "status": "paused"},
            ]
        )
    )

    exit_code = main(["validate", str(spec_path), str(rows_dir)])

    assert exit_code == 0


def test_validate_rejects_single_rows_file_with_folder_help(tmp_path, capsys) -> None:
    spec_path = tmp_path / "dataset_spec.json"
    rows_path = tmp_path / "customers.json"
    spec_path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "name": "customers",
                        "row_count": 1,
                        "fields": [{"name": "customer_id", "data_type": "integer"}],
                    }
                ]
            }
        )
    )
    rows_path.write_text(json.dumps([{"customer_id": 1}]))

    exit_code = main(["validate", str(spec_path), str(rows_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "validate expects a dataset output folder" in captured.err


def test_validate_rejects_removed_spec_with_migration_help(tmp_path, capsys) -> None:
    spec_path = tmp_path / "removed_spec.json"
    rows_path = tmp_path / "rows"
    rows_path.mkdir()
    spec_path.write_text(
        json.dumps(
            {
                "seed": 11,
                "output_format": "json",
                "table": {
                    "name": "customers",
                    "row_count": 1,
                    "columns": [
                        {"name": "customer_id", "data_type": "integer", "strategy": "sequence"},
                    ],
                },
            }
        )
    )
    (rows_path / "customers.json").write_text(json.dumps([{"customer_id": 1}]))

    exit_code = main(["validate", str(spec_path), str(rows_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "GenerationSpec was removed in 0.6.0" in captured.err
    assert "operations/migrating-to-0.6/" in captured.err


def test_generate_rejects_removed_spec_before_writing_output(tmp_path, capsys) -> None:
    spec_path = tmp_path / "removed_spec.json"
    output_path = tmp_path / "out"
    spec_path.write_text(
        json.dumps(
            {
                "seed": 11,
                "output_format": "json",
                "table": {
                    "name": "customers",
                    "row_count": 2,
                    "columns": [
                        {"name": "customer_id", "data_type": "integer", "strategy": "sequence"},
                        {"name": "status", "data_type": "string", "strategy": "choice", "choices": ["new", "active"]},
                    ],
                },
            }
        )
    )

    exit_code = main(["generate", str(spec_path), "--output", str(output_path)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "GenerationSpec was removed in 0.6.0" in captured.err
    assert "operations/migrating-to-0.6/" in captured.err
    assert not output_path.exists()


def test_generate_from_csv_applies_business_rules_via_neutral_rules_helper(tmp_path) -> None:
    output_path = tmp_path / "out" / "customers.json"
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """
field_rules:
  - table: customers
    field: status
    required: true
    allowed_values: [new, active, paused]
"""
    )

    exit_code = main(
        [
            "generate-from-csv",
            str(FIXTURE_CUSTOMERS),
            "--count",
            "5",
            "--mode",
            "valid",
            "--seed",
            "9",
            "--format",
            "json",
            "--output",
            str(output_path),
            "--business-rules",
            str(rules_path),
        ]
    )

    report = json.loads((output_path.parent / "business_validation_report.json").read_text())

    assert exit_code == 0
    assert report["valid"] is True
    assert report["rule_fail_count"] == 0


def test_generate_from_csv_routes_through_dataset_command_helper(tmp_path) -> None:
    output_path = tmp_path / "out" / "customers.json"

    exit_code = main(
        [
            "generate-from-csv",
            str(FIXTURE_CUSTOMERS),
            "--count",
            "3",
            "--mode",
            "valid",
            "--seed",
            "15",
            "--format",
            "json",
            "--output",
            str(output_path),
            "--table",
            "customers_cli",
        ]
    )

    rows = json.loads(output_path.read_text())
    profile = json.loads((output_path.parent / "csv_profile.json").read_text())

    assert exit_code == 0
    assert len(rows) == 3
    assert profile["entities"][0]["name"] == "customers_cli"


def test_missing_csv_reports_friendly_error_without_traceback(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "profile-csv",
            str(tmp_path / "missing.csv"),
            "--output",
            str(tmp_path / "profile.json"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Error: file not found:" in captured.err
    assert "Traceback" not in captured.err


def test_generate_from_csv_refuses_to_overwrite_existing_output(tmp_path, capsys) -> None:
    output_path = tmp_path / "customers.csv"
    output_path.write_text("existing")

    exit_code = main(
        [
            "generate-from-csv",
            str(FIXTURE_CUSTOMERS),
            "--count",
            "3",
            "--seed",
            "15",
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "output already exists" in captured.err
    assert output_path.read_text() == "existing"


def test_generate_from_csv_overwrite_replaces_existing_output(tmp_path, capsys) -> None:
    output_path = tmp_path / "customers.csv"
    output_path.write_text("existing")

    exit_code = main(
        [
            "generate-from-csv",
            str(FIXTURE_CUSTOMERS),
            "--count",
            "3",
            "--seed",
            "15",
            "--format",
            "csv",
            "--output",
            str(output_path),
            "--overwrite",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated synthetic dataset:" in captured.err
    assert "source rows copied: no" in captured.err
    assert len(list(csv.DictReader(output_path.open()))) == 3


def load_csv_folder(folder: Path) -> dict[str, list[dict[str, str]]]:
    rows = {}
    for path in folder.glob("*.csv"):
        with path.open(newline="") as handle:
            rows[path.stem] = list(csv.DictReader(handle))
    return rows


def copied_rows(generated: dict[str, list[dict[str, str]]], source: dict[str, list[dict[str, str]]]) -> bool:
    for table, rows in generated.items():
        generated_normalized = {tuple(row.items()) for row in rows}
        source_normalized = {tuple(row.items()) for row in source.get(table, [])}
        if generated_normalized & source_normalized:
            return True
    return False


def test_validate_prints_human_summary_to_stderr(tmp_path, capsys) -> None:
    spec_path = tmp_path / "dataset_spec.yaml"
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    spec_path.write_text(
        """
entities:
  - name: customers
    row_count: 1
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
"""
    )
    (rows_dir / "customers.json").write_text(json.dumps([{"customer_id": 1}]))

    exit_code = main(["validate", str(spec_path), str(rows_dir)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Validation passed:" in captured.err
    assert json.loads(captured.out)["valid"] is True
