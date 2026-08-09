from __future__ import annotations

import csv
from io import StringIO

import pytest

from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_dataset_generation_artifacts
from test_data_agent.io.writers import (
    quote_sql_identifier,
    rows_to_csv,
    rows_to_sql,
    sql_literal,
    write_dataset_rows,
)


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
