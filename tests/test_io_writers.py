from __future__ import annotations

import pytest

from test_data_agent.io.writers import quote_sql_identifier, rows_to_sql, sql_literal


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
