"""Fictional exact-decimal spec, generation, validation and export."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.writers import write_dataset_rows, write_parquet
from test_data_agent.postgres_sql_export import PostgresSqlExportError, postgres_literal, render_postgres_sql
from test_data_agent.safety import SpecSafetyError, assert_spec_safe
from test_data_agent.validation.schema_validator import validate_schema


def _spec(*, precision: int = 38, scale: int = 16) -> DatasetSpec:
    value = "9007199254740993." + "1" * scale
    return DatasetSpec(schema_version="1.1", entities=[EntitySpec(
        name="fictional_items", row_count=3,
        fields=[FieldSpec(
            name="synthetic_amount", data_type="decimal",
            distribution={"kind": "decimal_range", "precision": precision,
                          "scale": scale, "min": value, "max": value},
        )],
    )])


def test_decimal_spec_generates_and_exports_exact_values(tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    spec = _spec()
    rows = generate_dataset(spec, seed=17)
    values = [row["synthetic_amount"] for row in rows["fictional_items"]]
    assert values == [Decimal("9007199254740993." + "1" * 16)] * 3
    assert validate_schema(rows, spec) == []

    write_dataset_rows(rows, OutputFormat.CSV, tmp_path / "csv", spec=spec)
    write_dataset_rows(rows, OutputFormat.JSON, tmp_path / "json", spec=spec)
    write_dataset_rows(rows, OutputFormat.PARQUET, tmp_path / "parquet", spec=spec)
    csv_rows = list(csv.DictReader(StringIO((tmp_path / "csv/fictional_items.csv").read_text())))
    json_rows = json.loads((tmp_path / "json/fictional_items.json").read_text())
    parquet_path = tmp_path / "parquet/fictional_items.parquet"
    assert [row["synthetic_amount"] for row in csv_rows] == [str(values[0])] * 3
    assert [row["synthetic_amount"] for row in json_rows] == [str(values[0])] * 3
    assert str(pq.read_schema(parquet_path).field("synthetic_amount").type) == "decimal128(38, 16)"
    assert [row["synthetic_amount"] for row in pq.read_table(parquet_path).to_pylist()] == values
    sql = render_postgres_sql(spec, rows)
    assert '"synthetic_amount" NUMERIC(38, 16)' in sql
    assert "9007199254740993.1111111111111111" in sql


def test_decimal_contract_rejects_missing_approximate_and_overprecision():
    with pytest.raises(ValueError):
        FieldSpec(name="amount", data_type="decimal")
    with pytest.raises(ValueError):
        FieldSpec(name="amount", data_type="decimal", distribution={
            "kind": "numeric", "min_value": 1.0, "max_value": 2.0,
        })
    with pytest.raises(ValueError):
        _spec(precision=39)
    with pytest.raises(ValueError, match="schema_version 1.1"):
        DatasetSpec(schema_version="1.0", entities=_spec().entities)


def test_decimal_spec_validation_does_not_echo_rejected_bound():
    marker = "12345678901234567890.123"
    with pytest.raises(ValueError) as error:
        DatasetSpec.model_validate({"schema_version": "1.1", "entities": [{
            "name": "fictional_items", "row_count": 1,
            "fields": [{"name": "amount", "data_type": "decimal", "distribution": {
                "kind": "decimal_range", "precision": 20, "scale": 2,
                "min": marker, "max": "2.00",
            }}],
        }]})
    assert marker not in str(error.value)
    assert "9007199254740993" not in repr(_spec())


def test_decimal_parquet_rejects_mismatched_value_without_publication(tmp_path):
    pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"
    output.write_bytes(b"previous fictional artifact")
    with pytest.raises(ValueError, match="^Parquet rows do not match declared field types$"):
        write_parquet(
            [{"synthetic_amount": Decimal("1.12345678901234567")}], output,
            fields=_spec().entities[0].fields,
        )
    assert output.read_bytes() == b"previous fictional artifact"


def test_decimal_parquet_accepts_canonical_csv_text(tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"
    value = "9007199254740993.1234567890123456"
    write_parquet([{"synthetic_amount": value}], output, fields=_spec().entities[0].fields)
    assert pq.read_table(output).to_pylist()[0]["synthetic_amount"] == Decimal(value)


def test_sensitive_decimal_range_does_not_bypass_source_free_policy():
    spec = _spec()
    spec.entities[0].fields[0].sensitive = True
    with pytest.raises(SpecSafetyError, match="unsafe distribution kind"):
        assert_spec_safe(spec)


def test_exact_decimal_formula_is_rejected_before_float_arithmetic():
    spec = _spec()
    spec.constraints = [Constraint(
        type=ConstraintType.FORMULA, entity="fictional_items",
        fields=["synthetic_amount"], expression="synthetic_amount * 1.1", confidence=1.0,
    )]
    with pytest.raises(SpecSafetyError, match="exact decimal constraints"):
        generate_dataset(spec, seed=17)


def test_postgres_decimal_literal_requires_declared_precision_and_scale():
    with pytest.raises(PostgresSqlExportError, match="decimal value is invalid"):
        postgres_literal(Decimal("1.25"), _spec().entities[0].fields[0].data_type)
    with pytest.raises(PostgresSqlExportError, match="decimal value is invalid"):
        postgres_literal(Decimal("1.234"), _spec().entities[0].fields[0].data_type,
                         precision=20, scale=2)
    assert postgres_literal("1.25", _spec().entities[0].fields[0].data_type,
                            precision=20, scale=2) == "1.25"
    with pytest.raises(PostgresSqlExportError, match="decimal value is invalid"):
        postgres_literal("1.25);DROP TABLE x;--", _spec().entities[0].fields[0].data_type,
                         precision=20, scale=2)


def test_fictional_cli_writes_exact_decimal_parquet(tmp_path: Path):
    pq = pytest.importorskip("pyarrow.parquet")
    spec = tmp_path / "fictional-spec.json"
    spec.write_text(json.dumps({
        "schema_version": "1.1", "entities": [{
            "name": "fictional_items", "row_count": 2, "fields": [
                {"name": "amount_small", "data_type": "decimal", "distribution": {
                    "kind": "decimal_range", "precision": 20, "scale": 2,
                    "min": "9007199254740993.25", "max": "9007199254740993.25",
                }},
                {"name": "amount_wide", "data_type": "decimal", "distribution": {
                    "kind": "decimal_range", "precision": 38, "scale": 16,
                    "min": "9007199254740993.1234567890123456",
                    "max": "9007199254740993.1234567890123456",
                }},
            ],
        }], "generation_settings": {"seed": 17, "output_format": "parquet"},
    }), encoding="utf-8")
    package_root = Path(os.environ.get(
        "TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT",
        str(Path(__file__).resolve().parents[1] / "src"),
    )).resolve(strict=True)
    env = {**os.environ, "PYTHONPATH": str(package_root), "PYTHONDONTWRITEBYTECODE": "1"}
    probe = subprocess.run(
        [sys.executable, "-c", "import test_data_agent; print(test_data_agent.__file__)"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode == 0
    assert Path(probe.stdout.strip()).resolve().is_relative_to(package_root)
    output = tmp_path / "generated"
    result = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "generate", str(spec),
         "--output", str(output)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, "fictional exact DECIMAL CLI generation failed"
    table = pq.read_table(output / "fictional_items.parquet")
    assert str(table.schema.field("amount_small").type) == "decimal128(20, 2)"
    assert str(table.schema.field("amount_wide").type) == "decimal128(38, 16)"
    assert table.to_pylist() == [{
        "amount_small": Decimal("9007199254740993.25"),
        "amount_wide": Decimal("9007199254740993.1234567890123456"),
    }] * 2
