from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, strategies as st

from test_data_agent.csv_profiler import profile_csv
from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    check_allowlist,
    mask_row,
    validate_safe_select,
)
from test_data_agent.trino_config import TrinoConfig


IDENTIFIER = st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,24}", fullmatch=True)
OUTSIDE_ALLOWLIST = IDENTIFIER.filter(
    lambda value: value
    not in {"analytics", "safe", "customers", "country_code"}
)
SENSITIVE_FIELD = st.sampled_from(
    ["email", "customer_email", "phone_number", "api_token", "ssn"]
)


@given(field=SENSITIVE_FIELD, alias=IDENTIFIER)
def test_safe_select_rejects_likely_pii_under_any_alias(field: str, alias: str) -> None:
    sql = (
        f'SELECT "{field}" AS "{alias}" '
        'FROM analytics.safe_schema.users LIMIT 1'
    )

    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql)


@given(keyword=st.sampled_from(["DROP TABLE", "DELETE FROM", "CALL"]), name=IDENTIFIER)
def test_safe_select_rejects_statement_injection_tails(keyword: str, name: str) -> None:
    sql = f"SELECT id FROM users LIMIT 1; {keyword} {name}"

    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql)


@given(
    boundary=st.sampled_from(["catalog", "schema"]),
    outside=OUTSIDE_ALLOWLIST,
    quote_parts=st.booleans(),
)
def test_safe_select_rejects_every_catalog_or_schema_allowlist_mismatch(
    boundary: str,
    outside: str,
    quote_parts: bool,
) -> None:
    catalog = outside if boundary == "catalog" else "analytics"
    schema = outside if boundary == "schema" else "safe"
    config = TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe"}),
    )
    if quote_parts:
        catalog = f'"{catalog}"'
        schema = f'"{schema}"'
    sql = f"SELECT synthetic_value FROM {catalog}.{schema}.records LIMIT 1"

    with pytest.raises(AllowlistError):
        validate_safe_select(sql, config=config)


@given(
    boundary=st.sampled_from(["table", "column"]),
    outside=OUTSIDE_ALLOWLIST,
)
def test_table_column_allowlist_requires_an_exact_qualified_match(
    boundary: str,
    outside: str,
) -> None:
    config = TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset(
            {"analytics.safe.customers.country_code"}
        ),
    )

    check_allowlist(
        catalog="analytics",
        schema="safe",
        table="customers",
        column="country_code",
        config=config,
    )
    with pytest.raises(AllowlistError):
        check_allowlist(
            catalog="analytics",
            schema="safe",
            table=outside if boundary == "table" else "customers",
            column=outside if boundary == "column" else "country_code",
            config=config,
        )


@given(header=IDENTIFIER)
def test_csv_profiler_rejects_duplicate_headers(header: str) -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "duplicate.csv"
        path.write_text(f"{header},{header}\n1,2\n")

        with pytest.raises(ValueError, match="unique"):
            profile_csv(path)


@given(value=st.from_regex(r"[A-Za-z0-9]{3,64}", fullmatch=True))
def test_sensitive_mask_never_returns_plain_value(value: str) -> None:
    masked = mask_row({"customer_email": value})["customer_email"]

    assert masked != value
