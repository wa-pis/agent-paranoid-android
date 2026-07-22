import csv
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from test_data_agent.cli import main
from test_data_agent.core.limits import InputLimitError
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.generator import generate_rows
from test_data_agent.io.writers import write_parquet
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


def test_csv_profile_detects_semicolon_delimiter_and_utf8_bom(tmp_path) -> None:
    source = tmp_path / "customers_semicolon.csv"
    source.write_bytes(
        "\ufeffcustomer_id;email;status\n"
        "1;alice@example.com;active\n"
        "2;bob@example.com;paused\n".encode("utf-8")
    )

    profile = profile_csv(source)

    assert [column.name for column in profile.columns] == ["customer_id", "email", "status"]
    email = next(column for column in profile.columns if column.name == "email")
    status = next(column for column in profile.columns if column.name == "status")
    assert email.sensitive is True
    assert status.top_values == [{"value": "active", "count": 1}, {"value": "paused", "count": 1}]
    assert "alice@example.com" not in profile.model_dump_json()


def test_csv_profile_masks_secret_in_neutrally_named_column(tmp_path: Path) -> None:
    source = tmp_path / "secrets.csv"
    source.write_text("value\nsk_live_51ABCDEF\nsk_live_51ABCDEF\n")

    profile = profile_csv(source)
    value = profile.columns[0]

    assert value.sensitive is True
    assert value.semantic_type == "secret"
    assert value.top_values == []
    assert value.masked_patterns == [{"pattern": "secret", "count": 2}]
    assert "sk_live_51ABCDEF" not in profile.model_dump_json()


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


def test_parquet_preserves_homogeneous_scalar_types(tmp_path: Path) -> None:
    output = tmp_path / "rows.parquet"
    write_parquet([{"id": 1, "active": True, "amount": 1.5}], output)

    schema = pq.read_schema(output)
    assert str(schema.field("id").type) == "int64"
    assert str(schema.field("active").type) == "bool"
    assert str(schema.field("amount").type) == "double"


def test_profile_csv_rejects_duplicate_headers(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    path.write_text("id,status,status\n1,active,paid\n")

    with pytest.raises(ValueError, match="unique"):
        profile_csv(path)


def test_csv_profile_rejects_input_above_file_size_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "large.csv"
    path.write_text("value\n" + "x" * 64 + "\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES", "32")

    with pytest.raises(InputLimitError, match="must be <= 32 bytes"):
        profile_csv(path)


def test_csv_profile_rejects_input_above_row_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "rows.csv"
    path.write_text("value\none\ntwo\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_ROWS", "1")

    with pytest.raises(InputLimitError, match="<= 1 rows"):
        profile_csv(path)


def test_csv_profile_rejects_input_above_column_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "columns.csv"
    path.write_text("one,two\n1,2\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_COLUMNS", "1")

    with pytest.raises(InputLimitError, match="<= 1 columns"):
        profile_csv(path)


def test_csv_profile_rejects_input_above_cell_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "cells.csv"
    path.write_text("one,two\n1,2\n3,4\n")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "3")

    with pytest.raises(InputLimitError, match="<= 3 cells"):
        profile_csv(path)


def test_csv_profile_rejects_symbolic_link_input(tmp_path: Path) -> None:
    target = tmp_path / "target.csv"
    link = tmp_path / "source.csv"
    target.write_text("value\nsafe\n")
    link.symlink_to(target)

    with pytest.raises(InputLimitError, match="symbolic link inputs are not allowed"):
        profile_csv(link)


FIXTURE_CSV = __import__("pathlib").Path(__file__).parent / "fixtures" / "customers.csv"
