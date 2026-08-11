from __future__ import annotations

from pathlib import Path

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.privacy import LocalCategoryField


def write_spec(path: Path) -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="account",
                row_count=3,
                primary_key="id",
                fields=[
                    FieldSpec(
                        name="id",
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldSpec(
                        name="status",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "active", "count": 2},
                                {"value": "paused", "count": 1},
                            ],
                        },
                    ),
                ],
            )
        ],
        local_category_fields=[
            LocalCategoryField(entity="account", field="status")
        ],
    )
    path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")


def test_export_postgres_sql_generates_one_deterministic_file(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    first = tmp_path / "first.sql"
    second = tmp_path / "second.sql"
    write_spec(spec_path)

    assert main(["export-postgres-sql", str(spec_path), "--seed", "41", "-o", str(first)]) == 0
    assert main(["export-postgres-sql", str(spec_path), "--seed", "41", "-o", str(second)]) == 0

    sql = first.read_text(encoding="utf-8")
    assert sql == second.read_text(encoding="utf-8")
    assert sql.startswith("BEGIN;")
    assert 'CREATE TABLE "account"' in sql
    assert sql.count('INSERT INTO "account"') == 3
    assert "'active'" in sql or "'paused'" in sql
    assert sql.endswith("COMMIT;\n")


def test_export_postgres_sql_refuses_existing_output_by_default(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec_path = tmp_path / "spec.json"
    output = tmp_path / "dataset.sql"
    write_spec(spec_path)
    output.write_text("existing\n", encoding="utf-8")

    assert main(["export-postgres-sql", str(spec_path), "-o", str(output)]) == 2

    assert output.read_text(encoding="utf-8") == "existing\n"
    assert "output already exists" in capsys.readouterr().err
