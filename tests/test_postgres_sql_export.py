from __future__ import annotations

import math
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.core.relationship import Relationship
from test_data_agent.postgres_sql_export import (
    PostgresSqlExportError,
    render_postgres_sql,
    write_postgres_sql,
)


def relational_spec() -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name='account"root',
                row_count=1,
                primary_key="id",
                fields=[
                    FieldSpec(
                        name="id",
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldSpec(name="tier", data_type=FieldType.STRING),
                    FieldSpec(name="active", data_type=FieldType.BOOLEAN),
                    FieldSpec(name="created_at", data_type=FieldType.DATETIME),
                ],
            ),
            EntitySpec(
                name="order",
                row_count=1,
                primary_key="id",
                fields=[
                    FieldSpec(
                        name="id",
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldSpec(
                        name="account_id",
                        data_type=FieldType.INTEGER,
                        sensitive=True,
                    ),
                    FieldSpec(name="amount", data_type=FieldType.FLOAT),
                    FieldSpec(name="due_date", data_type=FieldType.DATE),
                    FieldSpec(
                        name="note",
                        data_type=FieldType.STRING,
                        nullable=True,
                    ),
                ],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity='account"root',
                parent_field="id",
                child_entity="order",
                child_field="account_id",
                confidence=1.0,
                status="declared",
            )
        ],
        local_category_fields=[
            LocalCategoryField(entity='account"root', field="tier")
        ],
    )


def generated_rows() -> dict[str, list[dict[str, object]]]:
    return {
        'account"root': [
            {
                "id": 7,
                "tier": "founder's",
                "active": True,
                "created_at": "2026-08-11T12:00:00+04:00",
            }
        ],
        "order": [
            {
                "id": 11,
                "account_id": 7,
                "amount": 12.5,
                "due_date": "2026-08-12",
                "note": None,
            }
        ],
    }


def test_renders_one_deterministic_dependency_ordered_postgres_transaction() -> None:
    spec = relational_spec()

    sql = render_postgres_sql(spec, generated_rows())

    assert sql == render_postgres_sql(spec, generated_rows())
    assert sql.startswith(
        'BEGIN;\n\nSET LOCAL standard_conforming_strings = on;\n\n'
        'CREATE TABLE "account""root"'
    )
    assert sql.index('CREATE TABLE "account""root"') < sql.index(
        'CREATE TABLE "order"'
    )
    assert 'PRIMARY KEY ("id")' in sql
    assert (
        'ALTER TABLE "order" ADD CONSTRAINT "fk_0001" '
        'FOREIGN KEY ("account_id") REFERENCES "account""root" ("id") '
        "DEFERRABLE INITIALLY DEFERRED;"
    ) in sql
    assert "VALUES (7, 'founder''s', TRUE, " in sql
    assert "TIMESTAMPTZ '2026-08-11 12:00:00+04:00'" in sql
    assert "VALUES (11, 7, 12.5, DATE '2026-08-12', NULL);" in sql
    assert sql.endswith("COMMIT;\n")


def test_generated_sql_parses_as_postgres_without_live_database() -> None:
    sqlglot = pytest.importorskip("sqlglot")

    statements = sqlglot.parse(render_postgres_sql(relational_spec(), generated_rows()), read="postgres")

    assert len(statements) == 8


def test_unsupported_value_keeps_existing_target_unchanged(tmp_path: Path) -> None:
    output = tmp_path / "dataset.sql"
    output.write_text("previous complete file\n", encoding="utf-8")
    rows = generated_rows()
    rows["order"][0]["amount"] = math.nan

    with pytest.raises(PostgresSqlExportError, match="float value"):
        write_postgres_sql(relational_spec(), rows, output)

    assert output.read_text(encoding="utf-8") == "previous complete file\n"
    assert list(tmp_path.iterdir()) == [output]


def test_sql_export_requires_sql_suffix(tmp_path: Path) -> None:
    with pytest.raises(PostgresSqlExportError, match=".sql suffix"):
        write_postgres_sql(
            relational_spec(),
            generated_rows(),
            tmp_path / "dataset.txt",
        )
