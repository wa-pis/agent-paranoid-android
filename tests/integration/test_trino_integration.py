import os
import json
import subprocess
import sys
from pathlib import Path

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

ROOT = Path(__file__).parents[2]


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


def test_local_trino_example_profiles_then_generates_from_installed_package(
    tmp_path: Path,
) -> None:
    output = tmp_path / "local-trino"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PATH"] = os.pathsep.join(
        [str(Path(sys.executable).parent), environment.get("PATH", "")]
    )

    subprocess.run(
        [sys.executable, ROOT / "examples/local_trino/run.py", output],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads((output / "example_result.json").read_text())
    profile_text = (output / "profile.json").read_text()
    manifest = json.loads(
        (output / "generated/generation_manifest.json").read_text()
    )
    assert result["catalog_available"] is True
    assert result["schema_available"] is True
    assert result["table_available"] is True
    assert result["profile_row_count"] == 25
    assert result["generated_row_counts"] == {"nation": 12}
    assert result["source_rows_copied"] is False
    assert result["validation_valid"] is True
    assert "ALGERIA" not in profile_text
    assert manifest["synthetic"] is True
    assert manifest["seed"] == 141421


def test_local_trino_query_example_is_source_free(tmp_path: Path) -> None:
    output = tmp_path / "local-trino-query"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PATH"] = os.pathsep.join(
        [str(Path(sys.executable).parent), environment.get("PATH", "")]
    )
    environment["TRINO_EXAMPLE_USE_QUERY"] = "true"
    environment["TRINO_ALLOWED_TABLE_COLUMNS"] = "tpch.tiny.nation.*"

    subprocess.run(
        [sys.executable, ROOT / "examples/local_trino/run.py", output],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    profile_text = (output / "profile.json").read_text()
    profile = json.loads(profile_text)
    result = json.loads((output / "example_result.json").read_text())
    manifest = json.loads(
        (output / "generated/generation_manifest.json").read_text()
    )
    assert profile["source_type"] == "trino_query"
    assert len(profile["source_fingerprint"]) == 64
    assert profile["source_policy_version"] == "1.0"
    assert "999999" not in profile_text
    assert result["query_source"] is True
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
