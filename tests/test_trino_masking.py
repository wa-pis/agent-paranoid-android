from __future__ import annotations

import ast
from dataclasses import replace
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
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudgetExceeded,
    with_query_work_budget,
)


def masker_config() -> TrinoConfig:
    return TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )


def masker_config_allowlisted_columns() -> TrinoConfig:
    return replace(
        masker_config(),
        allowed_table_columns=frozenset({"analytics.safe_schema.customers.country_code"}),
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


def test_masker_profile_column_safe_skips_top_values_for_disallowed_table_column() -> None:
    queries: list[TrinoQuery] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        if "GROUP BY" in query.sql:
            return [{"value": "allowed", "count": 2}]
        return [
            {
                "row_count": 10,
                "non_null_count": 10,
                "approx_distinct_count": 2,
            }
        ]

    profile = TrinoMasker(
        config=masker_config_allowlisted_columns(),
        fetch_query=fetch_query,
        fetch_sql=reject_sql,
    ).profile_column_safe(
        "analytics",
        "safe_schema",
        "customers",
        "region_code",
        "varchar",
        False,
        20,
    )

    assert "top_values" not in profile
    assert len(queries) == 1
    assert "GROUP BY" not in queries[0].sql


def test_masker_profile_column_safe_returns_top_values_for_allowlisted_table_column() -> None:
    queries: list[TrinoQuery] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        if "GROUP BY" in query.sql:
            return [{"value": "allowed", "count": 2}, {"value": "other", "count": 1}]
        return [
            {
                "row_count": 10,
                "non_null_count": 10,
                "approx_distinct_count": 2,
            }
        ]

    profile = TrinoMasker(
        config=masker_config_allowlisted_columns(),
        fetch_query=fetch_query,
        fetch_sql=reject_sql,
    ).profile_column_safe(
        "analytics",
        "safe_schema",
        "customers",
        "country_code",
        "varchar",
        False,
        20,
    )

    assert profile["top_values"] == [
        {"value": "category_1", "count": 2},
        {"value": "category_2", "count": 1},
    ]
    assert len(queries) == 2
    assert any("GROUP BY" in query.sql for query in queries)


def test_masker_suppresses_sensitive_numeric_summaries_at_query_boundary() -> None:
    queries: list[TrinoQuery] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        return [
            {
                "row_count": 10,
                "non_null_count": 10,
                "approx_distinct_count": 10,
                "max_abs_magnitude": 8,
                "has_negative": False,
                "has_positive": True,
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
        "tax_id",
        "bigint",
        False,
        20,
    )

    assert profile["sensitive"] is True
    assert not {"min_value", "max_value", "p05", "p95"} & profile.keys()
    assert profile["numeric_shape"] == {
        "max_abs_magnitude": 8,
        "has_negative": False,
        "has_positive": True,
    }
    assert all(
        expression not in queries[0].sql
        for expression in ("min(", "approx_percentile(")
    )


def test_safe_select_masks_every_returned_string() -> None:
    source_values = {"Jane Doe", "14 Elm Crescent", "ordinary note"}
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=lambda _sql: [
            {
                "label": "Jane Doe",
                "location": "14 Elm Crescent",
                "note": "ordinary note",
                "count": 3,
            }
        ],
    )

    result = masker.run_safe_select(
        "SELECT label, location, note, count "
        "FROM analytics.safe_schema.customers LIMIT 1"
    )

    assert result == [
        {
            "label": "[MASKED]",
            "location": "[MASKED]",
            "note": "[MASKED]",
            "count": 3,
        }
    ]
    assert all(value not in str(result) for value in source_values)


def test_safe_select_masks_strings_in_nested_values() -> None:
    source_values = {"ordinary note", "nested label", "tuple label"}
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=lambda _sql: [
            {
                "payload": {
                    "note": "ordinary note",
                    "items": ["nested label", 3],
                    "pair": ("tuple label", 4),
                },
                "count": 2,
            }
        ],
    )

    result = masker.run_safe_select(
        "SELECT payload, count FROM analytics.safe_schema.customers LIMIT 1"
    )

    assert result == [
        {
            "payload": {
                "note": "[MASKED]",
                "items": ["[MASKED]", 3],
                "pair": ("[MASKED]", 4),
            },
            "count": 2,
        }
    ]
    assert all(value not in str(result) for value in source_values)


@pytest.mark.parametrize(
    ("limit_name", "limit", "payload", "message"),
    [
        (
            "TEST_DATA_AGENT_MAX_JSON_DEPTH",
            2,
            {"outer": {"value": "hidden"}},
            "Trino safe-select result values must have depth <= 2",
        ),
        (
            "TEST_DATA_AGENT_MAX_INPUT_CELLS",
            2,
            ["first", "second"],
            "Trino safe-select result contains too many values",
        ),
    ],
)
def test_safe_select_rejects_excessive_nested_complexity(
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    limit: int,
    payload: Any,
    message: str,
) -> None:
    monkeypatch.setenv(limit_name, str(limit))
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=lambda _sql: [{"payload": payload}],
    )

    with pytest.raises(ValueError, match=f"^{message}$"):
        masker.run_safe_select(
            "SELECT payload FROM analytics.safe_schema.customers LIMIT 1"
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


def test_masker_rejects_ast_budget_before_fetch() -> None:
    masker = TrinoMasker(
        config=masker_config(),
        fetch_query=reject_query,
        fetch_sql=reject_sql,
    )
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, ast_nodes=1)
    run_safe_select = with_query_work_budget(masker.run_safe_select, limits)

    with pytest.raises(QueryWorkBudgetExceeded, match="AST nodes"):
        run_safe_select(
            "SELECT synthetic_id FROM analytics.safe_schema.customers LIMIT 1"
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
