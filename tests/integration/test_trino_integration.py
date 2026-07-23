import os

import pytest

from test_data_agent.mcp_trino_server import (
    describe_table,
    list_catalogs,
    list_schemas,
    list_tables,
    profile_table_safe,
    run_safe_select,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("TEST_TRINO_INTEGRATION") != "1",
        reason="set TEST_TRINO_INTEGRATION=1 with a local Trino service",
    ),
]


def test_trino_metadata_and_safe_profile_round_trip() -> None:
    assert "tpch" in list_catalogs()
    assert "tiny" in list_schemas("tpch")
    assert "nation" in list_tables("tpch", "tiny")

    description = describe_table("tpch", "tiny", "nation")
    assert {column["column_name"] for column in description} >= {
        "nationkey",
        "regionkey",
    }

    profile = profile_table_safe("tpch", "tiny", "nation", max_top_values=5)
    assert profile["source_type"] == "trino"
    assert profile["row_count"] == 25
    assert profile["columns"]


def test_trino_safe_select_returns_only_bounded_requested_columns() -> None:
    rows = run_safe_select(
        "SELECT nationkey, regionkey "
        "FROM tpch.tiny.nation "
        "LIMIT 3"
    )

    assert len(rows) == 3
    assert all(set(row) == {"nationkey", "regionkey"} for row in rows)
