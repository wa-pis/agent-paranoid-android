from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, strategies as st

from test_data_agent.csv_profiler import profile_csv
from test_data_agent.mcp_trino_server import SqlSafetyError, mask_row, validate_safe_select


IDENTIFIER = st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,24}", fullmatch=True)
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
