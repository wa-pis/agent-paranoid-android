"""Owned Trino lifecycle uses fictional drivers only."""
import multiprocessing
import time
from dataclasses import replace
from functools import partial

import pytest

pytest.importorskip("pyarrow")

from tests.test_transformation_query_capture import setup
from tests.test_trino_client import FakeCursor, FakeDriver, client_config
from test_data_agent.io.transformation_trino_stream import _TrinoCapture, _capture_trino_isolated
from test_data_agent.sql_query_source import SqlQueryAdapter


def _fictional_trino(fault):
    class Cursor(FakeCursor):
        def execute(self, sql, parameters):
            self.row_offset = 0
            self.metadata = "information_schema.columns" in sql
            self.no_rows = sql.endswith("WHERE FALSE")
            if fault == "backend":
                raise RuntimeError("fictional backend canary")
            if self.metadata:
                self.rows = [("status", "varchar", "NO")]
                self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
            else:
                self.rows = [] if self.no_rows else [("alpha", 2), ("beta", 1)]
                self.description = [("label", "varchar"), ("measured", "bigint")]

        def fetchmany(self, size):
            if ((fault == "metadata" and self.metadata)
                    or (fault == "rows" and not self.metadata and not self.no_rows)):
                while True:
                    time.sleep(1)
            return super().fetchmany(size)

    return FakeDriver(Cursor([]))


@pytest.mark.parametrize("fault", [None, "metadata", "rows", "backend"])
def test_trino_owned_capture_reaps_blocked_metadata_and_rows(tmp_path, fault):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.TRINO)
    config = replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.*"}))
    capture = _TrinoCapture(request, config, "warehouse", kwargs["policy"], 3, 16384)
    before = {child.pid for child in multiprocessing.active_children()}
    if fault is None:
        source = _capture_trino_isolated(capture, driver_factory=partial(_fictional_trino, fault),
            max_seconds=10)
        assert source.payload
    else:
        with pytest.raises(ValueError, match="^invalid isolated Trino capture$") as caught:
            _capture_trino_isolated(capture, driver_factory=partial(_fictional_trino, fault),
                max_seconds=3)
        assert "canary" not in str(caught.value)
    assert {child.pid for child in multiprocessing.active_children()} <= before
