from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import pytest

from test_data_agent.core.settings import OutputFormat
from test_data_agent.core.field import FieldSpec
from test_data_agent.io.artifacts import write_dataset_generation_artifacts
from test_data_agent.io.writers import (
    quote_sql_identifier,
    rows_to_csv,
    rows_to_sql,
    sql_literal,
    write_dataset_rows,
    write_parquet,
)


def test_parquet_declared_schema_preserves_temporal_and_nullable_types(tmp_path: Path) -> None:
    pq = pytest.importorskip("pyarrow.parquet")
    fields = [
        FieldSpec(name="id", data_type="integer"),
        FieldSpec(name="active", data_type="boolean"),
        FieldSpec(name="amount", data_type="float"),
        FieldSpec(name="label", data_type="string"),
        FieldSpec(name="event_date", data_type="date"),
        FieldSpec(name="event_at", data_type="datetime"),
        FieldSpec(name="optional", data_type="integer", nullable=True),
    ]
    output = tmp_path / "rows.parquet"
    write_parquet([{
        "id": 2**53 + 1, "active": True, "amount": 1.5,
        "label": "fictional", "event_date": "2024-01-02",
        "event_at": "2024-01-02T03:04:05+03:00", "optional": None,
    }], output, fields=fields)

    schema = pq.read_schema(output)
    row = pq.read_table(output).to_pylist()[0]
    assert [str(field.type) for field in schema] == [
        "int64", "bool", "double", "string", "date32[day]",
        "timestamp[us, tz=+03:00]", "int64",
    ]
    assert row["id"] == 2**53 + 1
    assert row["event_date"] == date(2024, 1, 2)
    assert row["event_at"] == datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=3)))
    assert row["optional"] is None


@pytest.mark.parametrize("existing", [False, True])
def test_parquet_declared_schema_rejects_invalid_type_before_publication(
    tmp_path: Path, existing: bool,
) -> None:
    pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"
    if existing:
        output.write_bytes(b"previous fictional artifact")

    with pytest.raises(ValueError, match="^Parquet rows do not match declared field types$"):
        write_parquet(
            [{"amount": "not-a-number"}], output,
            fields=[FieldSpec(name="amount", data_type="integer")],
        )

    if existing:
        assert output.read_bytes() == b"previous fictional artifact"
    else:
        assert not output.exists()


@pytest.mark.parametrize("rows", [[], [{"event_date": None}]])
def test_parquet_declared_schema_keeps_type_without_values(
    tmp_path: Path, rows: list[dict[str, object]],
) -> None:
    pq = pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"

    write_parquet(
        rows, output,
        fields=[FieldSpec(name="event_date", data_type="date", nullable=True)],
    )

    assert str(pq.read_schema(output).field("event_date").type) == "date32[day]"
    assert pq.read_table(output).num_rows == len(rows)


def test_parquet_rejects_mixed_timestamp_offsets_without_partial_file(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"

    with pytest.raises(ValueError, match="^Parquet rows do not match declared field types$"):
        write_parquet(
            [{"at": "2024-01-01T01:00:00+01:00"},
             {"at": "2024-01-01T02:00:00+02:00"}],
            output,
            fields=[FieldSpec(name="at", data_type="datetime")],
        )

    assert not output.exists()


def test_parquet_without_spec_rejects_mixed_types_instead_of_stringifying(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow.parquet")
    output = tmp_path / "rows.parquet"

    with pytest.raises(ValueError, match="^Parquet rows have mixed field types$"):
        write_parquet([{"amount": 3}, {"amount": "not-a-number"}], output)

    assert not output.exists()


def test_csv_writer_neutralizes_formula_cells_and_headers() -> None:
    payload = rows_to_csv(
        [
            {
                "=header": "=SUM(A1:A2)",
                "advisor": "+cmd",
                "minus_number": -7,
                "semantic_provider": "-7",
                "categorical": " @formula",
                "tab": "\tformula",
                "safe": "synthetic",
            }
        ]
    )

    rows = list(csv.reader(StringIO(payload)))

    assert rows[0][0] == "'=header"
    assert rows[1] == [
        "'=SUM(A1:A2)",
        "'+cmd",
        "-7",
        "'-7",
        "' @formula",
        "'\tformula",
        "synthetic",
    ]


@pytest.mark.parametrize(
    "artifact_name",
    ["../source-marker.json", "nested/profile.json", ".", ".."],
)
def test_generation_artifacts_reject_unsafe_profile_name_before_writes(
    tmp_path,
    artifact_name: str,
) -> None:
    with pytest.raises(ValueError, match="^unsafe artifact name$"):
        write_dataset_generation_artifacts(
            object(),  # type: ignore[arg-type]
            object(),  # type: ignore[arg-type]
            object(),
            tmp_path / "rows.csv",
            profile_artifact_name=artifact_name,
        )

    assert list(tmp_path.iterdir()) == []


def test_dataset_writer_rejects_reserved_entity_before_writes(tmp_path) -> None:
    with pytest.raises(ValueError, match="reserved entity name"):
        write_dataset_rows(
            {
                "orders": [{"id": 1}],
                "generation_manifest": [{"id": 2}],
            },
            OutputFormat.JSON,
            tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_sql_writer_quotes_identifiers_and_escapes_literals() -> None:
    sql = rows_to_sql(
        'support"tickets',
        [
            {
                'ticket"id': 7,
                "summary": "customer's synthetic issue",
                "resolved": True,
                "closed_at": None,
            }
        ],
    )

    assert sql == (
        'INSERT INTO "support""tickets" '
        '("ticket""id", "summary", "resolved", "closed_at") '
        "VALUES (7, 'customer''s synthetic issue', TRUE, NULL);\n"
    )


def test_sql_writer_rejects_invalid_values_without_accepting_expressions() -> None:
    assert sql_literal("NOW(); DROP TABLE users") == "'NOW(); DROP TABLE users'"
    with pytest.raises(ValueError, match="non-finite"):
        sql_literal(float("inf"))
    with pytest.raises(ValueError, match="NUL"):
        quote_sql_identifier("unsafe\x00name")
