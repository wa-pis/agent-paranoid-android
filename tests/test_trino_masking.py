from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from test_data_agent import mcp_trino_server, trino_masking
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_masking import (
    TrinoMasker,
    mask_row,
    summarize_top_values,
)
from test_data_agent.trino_query_builders import TrinoQuery
from test_data_agent.trino_sql_policy import AllowlistError, SqlSafetyError


def masker_config() -> TrinoConfig:
    return TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )


def reject_query(query: TrinoQuery) -> list[dict[str, Any]]:
    raise AssertionError(f"query must not execute: {query.sql}")


def reject_sql(sql: str) -> list[dict[str, Any]]:
    raise AssertionError(f"SQL must not execute: {sql}")


def synthetic_secret() -> str:
    return "".join(("sk", "_live_", "51ABCDEF"))


def test_mask_row_detects_sensitive_names_and_neutral_values() -> None:
    assert mask_row(
        {
            "customer_email": "person@example.com",
            "value": synthetic_secret(),
            "status": "paid",
        }
    ) == {
        "customer_email": "[MASKED]",
        "value": "[MASKED]",
        "status": "paid",
    }


def test_safe_category_summary_never_returns_source_values() -> None:
    source_values = ["paid", "cancelled"]

    summary = summarize_top_values(
        [
            {"value": source_values[0], "count": 7},
            {"value": source_values[1], "count": 3},
        ]
    )

    assert summary == {
        "top_values": [
            {"value": "category_1", "count": 7},
            {"value": "category_2", "count": 3},
        ]
    }
    assert all(value not in str(summary) for value in source_values)


def test_sensitive_category_summary_returns_patterns_only() -> None:
    secret = synthetic_secret()

    summary = summarize_top_values([{"value": secret, "count": 2}])

    assert summary == {
        "sensitive": True,
        "semantic_type": "secret",
        "masked_patterns": [{"pattern": "secret", "count": 2}],
    }
    assert secret not in str(summary)


def test_masker_skips_category_query_for_sensitive_column_name() -> None:
    queries: list[TrinoQuery] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        return [
            {
                "row_count": 10,
                "non_null_count": 10,
                "approx_distinct_count": 2,
            }
        ]

    profile = TrinoMasker(
        config=masker_config(),
        fetch_query=fetch_query,
        fetch_sql=reject_sql,
    ).profile_column_safe(
        "analytics",
        "safe_schema",
        "customers",
        "customer_email",
        "varchar",
        False,
        20,
    )

    assert profile["sensitive"] is True
    assert len(queries) == 1
    assert "GROUP BY" not in queries[0].sql


def test_masker_masks_samples_before_returning_them() -> None:
    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        assert "LIMIT 1" in query.sql
        return [{"value": "person@example.com", "status": "paid"}]

    rows = TrinoMasker(
        config=masker_config(),
        fetch_query=fetch_query,
        fetch_sql=reject_sql,
    ).sample_rows_masked(
        "analytics",
        "safe_schema",
        "customers",
        ["value", "status"],
        1,
    )

    assert rows == [{"value": "[MASKED]", "status": "paid"}]


def test_masker_rejects_unsafe_source_before_fetch() -> None:
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=reject_sql,
    )

    with pytest.raises(AllowlistError, match="catalog is not allowed"):
        masker.sample_rows_masked(
            "production",
            "safe_schema",
            "customers",
            ["status"],
            1,
        )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM analytics.safe_schema.customers",
        "SELECT * FROM analytics.safe_schema.customers LIMIT 1",
        ("SELECT customer_email AS value FROM analytics.safe_schema.customers LIMIT 1"),
        "SELECT synthetic_id FROM analytics.safe_schema.customers",
        (
            "SELECT synthetic_id FROM analytics.safe_schema.customers "
            "ORDER BY rand() LIMIT 1"
        ),
        (
            "SELECT synthetic_id FROM analytics.safe_schema.customers LIMIT 1; "
            "DROP TABLE customers"
        ),
    ],
)
def test_masker_rejects_unsafe_sql_before_fetch(sql: str) -> None:
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=reject_sql,
    )

    with pytest.raises(SqlSafetyError):
        masker.run_safe_select(sql)


def test_masker_rejects_disallowed_sql_source_before_fetch() -> None:
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=reject_sql,
    )

    with pytest.raises(AllowlistError, match="catalog is not allowed"):
        masker.run_safe_select(
            "SELECT synthetic_id FROM production.safe_schema.customers LIMIT 1"
        )


def test_server_keeps_masking_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoMasker is TrinoMasker
    assert mcp_trino_server.mask_row is mask_row
    assert mcp_trino_server.summarize_top_values is summarize_top_values


def test_masking_boundary_does_not_import_transport_or_client() -> None:
    module_path = Path(trino_masking.__file__)
    tree = ast.parse(module_path.read_text())
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "test_data_agent.mcp_trino_server" not in imported_modules
    assert "test_data_agent.mcp_trino_transport" not in imported_modules
    assert "test_data_agent.trino_client" not in imported_modules
