import pytest
from pydantic import ValidationError

from test_data_agent.generator import generate_rows
from test_data_agent.spec import ColumnSpec, DataType, GenerationSpec, TableSpec
from test_data_agent.validator import validate_rows, validate_rows_report


def make_spec(seed: int = 123) -> GenerationSpec:
    return GenerationSpec(
        seed=seed,
        table=TableSpec(
            name="customers",
            row_count=5,
            columns=[
                ColumnSpec(name="id", data_type=DataType.INTEGER, strategy="sequence"),
                ColumnSpec(name="email", data_type=DataType.EMAIL),
                ColumnSpec(name="status", data_type=DataType.STRING, strategy="choice", choices=["new", "active"]),
                ColumnSpec(name="score", data_type=DataType.FLOAT, min_value=0, max_value=1),
            ],
        ),
    )


def test_generation_is_deterministic_for_seed() -> None:
    spec = make_spec(seed=42)

    assert generate_rows(spec) == generate_rows(spec)
    assert generate_rows(spec) != generate_rows(make_spec(seed=43))


def test_generated_rows_match_requested_schema() -> None:
    spec = make_spec()
    rows = generate_rows(spec)

    assert len(rows) == 5
    assert list(rows[0].keys()) == ["id", "email", "status", "score"]
    assert [row["id"] for row in rows] == [1, 2, 3, 4, 5]
    assert validate_rows(rows, spec) == []


def test_sensitive_fields_are_inferred_conservatively() -> None:
    assert ColumnSpec(name="customer_email", data_type=DataType.EMAIL).sensitive is True
    assert ColumnSpec(name="api_token", data_type=DataType.STRING).sensitive is True
    assert ColumnSpec(name="favorite_color", data_type=DataType.STRING).sensitive is False


def test_mock_profile_builds_spec_without_source_rows() -> None:
    spec = GenerationSpec.from_mock_profile(
        {
            "table": "orders",
            "columns": [
                {"name": "order_id", "data_type": "bigint"},
                {"name": "customer_email", "data_type": "varchar"},
                {"name": "amount", "data_type": "double", "min_value": 1, "max_value": 10},
            ],
        },
        seed=7,
        row_count=3,
    )

    rows = generate_rows(spec)

    assert spec.table.name == "orders"
    assert spec.table.columns[1].sensitive is True
    assert validate_rows(rows, spec) == []


def test_invalid_choice_strategy_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ColumnSpec(name="status", data_type=DataType.STRING, strategy="choice")


def test_trino_profile_infers_generation_spec_from_safe_metadata() -> None:
    spec = GenerationSpec.from_trino_profile(
        {
            "table": "events",
            "columns": [
                {
                    "name": "status",
                    "data_type": "varchar",
                    "top_values": [{"value": "new", "count": 10}, {"value": "done", "count": 7}],
                    "approx_distinct_count": 2,
                },
                {
                    "name": "amount",
                    "data_type": "double",
                    "min_value": 0,
                    "p05": 10,
                    "p95": 20,
                    "max_value": 999,
                },
                {
                    "name": "created_at",
                    "data_type": "timestamp",
                    "min_timestamp": "2024-01-01T00:00:00",
                    "max_timestamp": "2024-01-02T00:00:00",
                },
                {
                    "name": "customer_email",
                    "data_type": "varchar",
                    "null_ratio": 0.25,
                },
            ],
        },
        seed=99,
        row_count=25,
    )

    rows = generate_rows(spec)

    status, amount, created_at, email = spec.table.columns
    assert status.choices == ["new", "done"]
    assert amount.min_value == 10
    assert amount.max_value == 20
    assert created_at.data_type == DataType.DATETIME
    assert email.data_type == DataType.EMAIL
    assert email.sensitive is True
    assert email.nullable is True
    assert email.null_probability == 0.25
    assert {row["status"] for row in rows} <= {"new", "done"}
    assert all(10 <= row["amount"] <= 20 for row in rows)
    assert validate_rows(rows, spec) == []


def test_nullable_ratio_generates_nulls_deterministically() -> None:
    spec = GenerationSpec.from_trino_profile(
        {
            "table": "users",
            "columns": [
                {"name": "nickname", "data_type": "varchar", "null_ratio": 1.0},
            ],
        },
        seed=1,
        row_count=3,
    )

    assert generate_rows(spec) == [{"nickname": None}, {"nickname": None}, {"nickname": None}]


def test_invalid_ratio_supports_mixed_mode_and_report_output() -> None:
    spec = GenerationSpec.from_trino_profile(
        {
            "table": "metrics",
            "columns": [
                {
                    "name": "score",
                    "data_type": "integer",
                    "p05": 1,
                    "p95": 5,
                    "invalid_ratio": 1.0,
                },
            ],
        },
        seed=3,
        row_count=4,
    )

    rows = generate_rows(spec)
    report = validate_rows_report(rows, spec)

    assert rows == [
        {"score": "not-a-number"},
        {"score": "not-a-number"},
        {"score": "not-a-number"},
        {"score": "not-a-number"},
    ]
    assert report.valid is False
    assert report.row_count == 4
    assert report.expected_row_count == 4
    assert report.error_count == 4
    assert report.model_dump()["errors"]
