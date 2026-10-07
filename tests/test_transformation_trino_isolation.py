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


@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_owned_trino_capture_review_and_exact_temporary_output(tmp_path, output_format):
    import csv
    import io
    import yaml
    import pyarrow.parquet as pq
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
    from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
    from test_data_agent.io.transformation_publish import temporary_csv_publication

    request, kwargs = setup(tmp_path, SqlQueryAdapter.TRINO)
    policy = kwargs["policy"]
    if output_format != "csv":
        output = {"format": output_format, "fields": [
            {"name": "label", "type": "string"}, {"name": "measured", "type": "integer"}]}
        if output_format == "postgresql_sql":
            output["table"] = "summary"
        policy = BehaviorPolicy.model_validate({**policy.model_dump(), "output": output})
    config = replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.*"}))
    source = _capture_trino_isolated(_TrinoCapture(request, config, "warehouse", policy, 3, 16384),
        driver_factory=partial(_fictional_trino, None), max_seconds=10)
    profile = _profile_transformation_source(source, policy, budget=GenerationBudget(5), max_bytes=16384)
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    material = prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(),
        source, (), max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_csv_publication(material, max_total_bytes=32768, max_review_bytes=8192,
            max_output_bytes=16384, budget=GenerationBudget(5)) as destination:
        if output_format == "csv":
            rows = list(csv.DictReader(io.StringIO((destination / "dataset.csv").read_text())))
            assert rows == [{"label": "gamma", "measured": "8"}, {"label": "delta", "measured": "7"}]
        elif output_format == "parquet":
            assert pq.read_table(destination / "dataset.parquet").to_pylist() == [
                {"label": "gamma", "measured": 8}, {"label": "delta", "measured": 7}]
        else:
            payload = (destination / "dataset.sql").read_text()
            assert "VALUES ('gamma', 8);" in payload and "VALUES ('delta', 7);" in payload
            assert "alpha" not in payload and "beta" not in payload
    assert not destination.parent.exists()
