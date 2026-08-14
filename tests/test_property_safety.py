import json
import string
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, strategies as st

import test_data_agent.mcp_trino_transport as mcp_transport
import test_data_agent.cli as cli_module
from test_data_agent.cli import main
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    check_allowlist,
    mask_row,
    validate_safe_select,
)
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    MIN_TRANSPORT_RESPONSE_BYTES,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
)


IDENTIFIER = st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,24}", fullmatch=True)
OUTSIDE_ALLOWLIST = IDENTIFIER.filter(
    lambda value: value
    not in {"analytics", "safe", "customers", "country_code"}
)
SENSITIVE_FIELD = st.sampled_from(
    ["email", "customer_email", "phone_number", "api_token", "ssn"]
)
ERROR_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " \n\r\t\x1b'\"\\/",
    min_size=1,
    max_size=64,
).map("SOURCE_SECRET_".__add__)


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


@given(
    limit=st.integers(min_value=1, max_value=512),
    overflow=st.integers(min_value=1, max_value=512),
)
def test_oversized_jsonrpc_payload_fails_before_structural_parsing(
    limit: int,
    overflow: int,
) -> None:
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, raw_transport_payload_bytes=limit)
    parsed: list[bytes] = []

    def reject_parse(raw_payload: bytes, budget: QueryWorkBudget) -> None:
        parsed.append(raw_payload)
        raise AssertionError(f"unexpected parser budget: {budget!r}")

    def budget_factory(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        return budget

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            mcp_transport,
            "_consume_json_structure",
            reject_parse,
        )
        with pytest.raises(QueryWorkBudgetExceeded) as raised:
            mcp_transport._bounded_session_message(
                b"x" * (limit + overflow),
                budget_factory,
            )

    assert raised.value.dimension is QueryWorkDimension.RAW_TRANSPORT_PAYLOAD_BYTES
    assert parsed == []


@given(method=IDENTIFIER)
def test_truncated_jsonrpc_is_charged_then_rejected(method: str) -> None:
    raw_payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method},
        separators=(",", ":"),
    ).encode()[:-1]
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        raw_transport_payload_bytes=len(raw_payload),
    )
    budgets: list[QueryWorkBudget] = []

    def budget_factory(raw_payload_bytes: int) -> QueryWorkBudget:
        budget = QueryWorkBudget(limits)
        budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
        budgets.append(budget)
        return budget

    with pytest.raises(json.JSONDecodeError):
        mcp_transport._bounded_session_message(raw_payload, budget_factory)

    assert budgets[0].snapshot().raw_transport_payload_bytes == len(raw_payload)


@given(
    capacity=st.integers(min_value=0, max_value=4096),
    data=st.data(),
)
def test_transport_response_budget_is_monotonic_and_fail_closed(
    capacity: int,
    data: st.DataObject,
) -> None:
    accepted = data.draw(st.integers(min_value=0, max_value=capacity))
    overflow = data.draw(
        st.integers(min_value=capacity - accepted + 1, max_value=8192)
    )
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        transport_response_bytes=MIN_TRANSPORT_RESPONSE_BYTES + capacity,
    )
    budget = QueryWorkBudget(limits)

    budget.consume_transport_response_bytes(accepted)
    assert budget.snapshot().transport_response_bytes == accepted

    with pytest.raises(QueryWorkBudgetExceeded) as raised:
        budget.consume_transport_response_bytes(overflow)

    assert raised.value.dimension is QueryWorkDimension.TRANSPORT_RESPONSE_BYTES
    assert budget.snapshot().transport_response_bytes == accepted


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


@given(secret=ERROR_TEXT, json_output=st.booleans())
def test_cli_redacts_every_unexpected_error_without_debug(
    secret: str,
    json_output: bool,
) -> None:
    def fail(_args: object) -> int:
        raise RuntimeError(secret)

    stdout = StringIO()
    stderr = StringIO()
    arguments = ["examples", "--json"] if json_output else ["examples"]
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(cli_module, "run_command", fail)
        monkeypatch.setattr(cli_module, "run_json_command", fail)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(arguments)

    rendered = stdout.getvalue() + stderr.getvalue()
    assert exit_code == 70
    assert secret not in rendered
    assert "Traceback" not in rendered
    assert "unexpected internal error" in rendered
