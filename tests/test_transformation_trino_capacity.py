"""Capture capacity is explicit and separate from aggregate profiling."""
from dataclasses import replace

import pytest

from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.io.transformation_trino_stream import _trino_capture_limits
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS


def inputs():
    config = TrinoConfig(host="fictional.invalid", port=443, user="fictional",
        http_scheme="https", allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}), max_result_rows=2)
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "fields": [{"entity": "orders", "field": "status",
        "sensitivity": "non_sensitive", "behavior": {"action": "drop"}}]})
    return config, policy


def test_capture_capacity_preserves_other_limits_and_defaults():
    config, policy = inputs()
    scoped, limits = _trino_capture_limits(config, policy, 1_000_000, 8 * 1024 * 1024)
    assert scoped.max_result_rows == 1_000_001
    assert config.max_result_rows == 2
    assert replace(scoped, max_result_rows=2) == config
    assert replace(limits, database_result_bytes=DEFAULT_QUERY_WORK_LIMITS.database_result_bytes) == DEFAULT_QUERY_WORK_LIMITS
    assert DEFAULT_QUERY_WORK_LIMITS.database_result_bytes == 4 * 1024 * 1024


@pytest.mark.parametrize("setting,rows,size", [
    ("TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS", 4, 100),
    ("TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_FILE_BYTES", 1, 4),
])
def test_capture_capacity_cannot_exceed_session(monkeypatch, setting, rows, size):
    config, policy = inputs()
    monkeypatch.setenv(setting, "3")
    with pytest.raises(TransformationLimitError):
        _trino_capture_limits(config, policy, rows, size)


@pytest.mark.parametrize("rows,size", [(True, 100), (1, False), (0, 100), (1, 0)])
def test_capture_capacity_rejects_malformed_values(rows, size):
    config, policy = inputs()
    with pytest.raises(ValueError):
        _trino_capture_limits(config, policy, rows, size)


@pytest.mark.parametrize("row_count", [3, 4])
def test_scoped_capture_exceeds_ordinary_rows_but_rejects_overflow(tmp_path, row_count):
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.io.transformation_trino_stream import _capture_trino_result
    from test_data_agent.sql_query_source import SqlQueryAdapter
    from tests.test_transformation_query_capture import setup
    from tests.test_trino_client import FakeCursor, FakeDriver, client_config

    request, kwargs = setup(tmp_path, SqlQueryAdapter.TRINO)
    config = replace(client_config(max_result_rows=2), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.*"}))

    class Cursor(FakeCursor):
        def execute(self, sql, parameters):
            self.row_offset = 0
            if "information_schema.columns" in sql:
                self.rows = [("status", "varchar", "NO")]
                self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
            else:
                self.rows = [] if sql.endswith("WHERE FALSE") else [("alpha", 2)] * row_count
                self.description = [("label", "varchar"), ("measured", "bigint")]

    cursor = Cursor([])
    driver = FakeDriver(cursor)
    arguments = dict(config=config, source_id="warehouse", policy=kwargs["policy"],
        max_rows=3, max_bytes=16384, budget=GenerationBudget(5), driver=driver)
    if row_count == 3:
        assert _capture_trino_result(request, **arguments).payload
    else:
        with pytest.raises(TransformationLimitError):
            _capture_trino_result(request, **arguments)
    assert config.max_result_rows == 2
    assert cursor.closed and driver.dbapi.connection.closed
