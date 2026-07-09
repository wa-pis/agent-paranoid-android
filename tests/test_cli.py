import csv
import json
from pathlib import Path

from test_data_agent.cli import main


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
    spec = json.loads((output_path.parent / "generation_spec.json").read_text())
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


def test_generate_from_profile_uses_dataset_pipeline_without_legacy_warning(tmp_path, capsys) -> None:
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

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deprecated GenerationSpec compatibility" not in captured.err


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


def test_generate_dataset_spec_does_not_warn_about_legacy_path(tmp_path, capsys) -> None:
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

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deprecated GenerationSpec compatibility" not in captured.err


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


def test_validate_legacy_spec_warns_about_deprecated_path(tmp_path, capsys) -> None:
    spec_path = tmp_path / "legacy_spec.json"
    rows_path = tmp_path / "rows.json"
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
    rows_path.write_text(json.dumps([{"customer_id": 1}]))

    exit_code = main(["validate", str(spec_path), str(rows_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deprecated GenerationSpec compatibility" in captured.err


def test_validate_legacy_spec_writes_report_to_output_file(tmp_path, capsys) -> None:
    spec_path = tmp_path / "legacy_spec.json"
    rows_path = tmp_path / "rows.json"
    output_path = tmp_path / "validation_report.json"
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
    rows_path.write_text(json.dumps([{"customer_id": 1}]))

    exit_code = main(["validate", str(spec_path), str(rows_path), "--output", str(output_path)])

    captured = capsys.readouterr()
    report = json.loads(output_path.read_text())

    assert exit_code == 0
    assert captured.out == ""
    assert "deprecated GenerationSpec compatibility" in captured.err
    assert report["valid"] is True


def test_generate_legacy_spec_uses_dataset_engine_with_warning(tmp_path, capsys) -> None:
    spec_path = tmp_path / "legacy_spec.json"
    output_path = tmp_path / "out" / "rows.json"
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
    rows = json.loads(output_path.read_text())

    assert exit_code == 0
    assert "deprecated GenerationSpec compatibility" in captured.err
    assert rows[0]["customer_id"] == 11000001
    assert {row["status"] for row in rows} <= {"new", "active"}


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
            str(Path("tests/fixtures/customers.csv")),
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
