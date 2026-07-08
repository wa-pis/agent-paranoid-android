import csv
import json

import pyarrow.parquet as pq

from test_data_agent.cli import main
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.generator import generate_rows
from test_data_agent.spec import DataType, GenerationSpec
from test_data_agent.validator import validate_rows_report


def test_csv_profile_uses_safe_metadata_and_masks_pii() -> None:
    profile = profile_csv(FIXTURE_CSV)
    profile_json = profile.model_dump_json()

    assert profile.table == "customers"
    assert profile.row_count == 5
    assert "alice@example.com" not in profile_json
    assert "+1-555-0101" not in profile_json

    email = next(column for column in profile.columns if column.name == "email")
    status = next(column for column in profile.columns if column.name == "status")
    total = next(column for column in profile.columns if column.name == "total")

    assert email.sensitive is True
    assert email.top_values == []
    assert email.masked_patterns == [{"pattern": "email", "count": 5}]
    assert status.top_values
    assert total.data_type == "float"
    assert total.p05 is not None
    assert total.p95 is not None


def test_csv_profile_infers_generation_spec_without_copying_rows() -> None:
    profile = profile_csv(FIXTURE_CSV)
    spec = GenerationSpec.from_csv_profile(profile.model_dump(), seed=10, row_count=12)
    rows = generate_rows(spec)
    report = validate_rows_report(rows, spec)

    email = next(column for column in spec.table.columns if column.name == "email")
    created_at = next(column for column in spec.table.columns if column.name == "created_at")

    assert email.data_type == DataType.EMAIL
    assert created_at.data_type == DataType.DATETIME
    assert report.valid is True
    assert all(row["email"] not in {"alice@example.com", "bob@example.com"} for row in rows)


def test_profile_csv_cli_writes_safe_profile(tmp_path) -> None:
    output = tmp_path / "profile.json"

    assert main(["profile-csv", str(FIXTURE_CSV), "--output", str(output)]) == 0

    profile = json.loads(output.read_text())
    assert profile["source_type"] == "csv"
    assert len(profile["entities"]) == 1
    assert profile["entities"][0]["name"] == "customers"
    assert profile["entities"][0]["row_count"] == 5
    assert "alice@example.com" not in output.read_text()


def test_generate_from_csv_cli_writes_csv_json_parquet_and_reports(tmp_path) -> None:
    csv_output = tmp_path / "out" / "customers.csv"
    json_output = tmp_path / "out_json" / "customers.json"
    parquet_output = tmp_path / "out_parquet" / "customers.parquet"

    common_args = [
        "generate-from-csv",
        str(FIXTURE_CSV),
        "--count",
        "20",
        "--mode",
        "mixed",
        "--invalid-ratio",
        "0.1",
        "--seed",
        "123",
    ]

    assert main([*common_args, "--format", "csv", "--output", str(csv_output)]) == 0
    assert main([*common_args, "--format", "json", "--output", str(json_output)]) == 0
    assert main([*common_args, "--format", "parquet", "--output", str(parquet_output)]) == 0

    with csv_output.open() as handle:
        csv_rows = list(csv.DictReader(handle))
    json_rows = json.loads(json_output.read_text())
    parquet_rows = pq.read_table(parquet_output).to_pylist()
    report = json.loads((csv_output.parent / "validation_report.json").read_text())
    spec = json.loads((csv_output.parent / "generation_spec.json").read_text())
    profile = json.loads((csv_output.parent / "csv_profile.json").read_text())

    assert len(csv_rows) == 20
    assert len(json_rows) == 20
    assert len(parquet_rows) == 20
    assert report["valid"] is False
    assert any(section["failed"] > 0 for section in report["sections"])
    assert spec["generation_settings"]["seed"] == 123
    assert spec["generation_settings"]["output_format"] == "csv"
    assert spec["generation_settings"]["mode"] == "mixed"
    assert spec["generation_settings"]["invalid_ratio"] == 0.1
    assert spec["entities"][0]["name"] == "customers"
    assert spec["entities"][0]["row_count"] == 20
    assert profile["source_type"] == "csv"
    assert profile["entities"][0]["name"] == "customers"
    assert "alice@example.com" not in (csv_output.parent / "csv_profile.json").read_text()


FIXTURE_CSV = __import__("pathlib").Path(__file__).parent / "fixtures" / "customers.csv"
