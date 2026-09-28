"""Fictional stream through authorization, snapshot review and temporary output."""

from contextlib import contextmanager
import io
import csv

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
from test_data_agent.io.transformation_publish import temporary_csv_publication
from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest, QuerySourceColumn

pa = pytest.importorskip("pyarrow")


def setup(tmp_path, adapter):
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    path = tmp_path / "query.sql"
    path.write_text(f"SELECT status AS label, COUNT(*) AS measured FROM {table} GROUP BY status")
    request = SqlQueryProfileRequest(adapter, "warehouse", "summary", path)
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "input_format": f"{adapter.value}_query",
        "fields": [{"entity": request.entity_name, "field": name, "sensitivity": "non_sensitive",
            "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                {"original": [a], "replacement": [b]} for a, b in pairs]}}}
            for name, pairs in [("label", [("alpha", "gamma"), ("beta", "delta")]),
                                ("measured", [(2, 8), (1, 7)])]]})
    schema = pa.schema([pa.field("label", pa.string(), nullable=False),
                        pa.field("measured", pa.int64(), nullable=False)])
    kwargs = dict(allowed_tables=frozenset({table}),
        source_columns=(QuerySourceColumn("status", "text", False),), schema=schema,
        policy=policy, max_rows=3, max_bytes=16384, budget=GenerationBudget(5))
    return request, kwargs


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_capture_to_review_to_temporary_output(tmp_path, adapter, output_format):
    request, kwargs = setup(tmp_path, adapter)
    if output_format != "csv":
        output = {"format": output_format, "fields": [
            {"name": "label", "type": "string"}, {"name": "measured", "type": "integer"}]}
        if output_format == "postgresql_sql":
            output["table"] = "summary"
        kwargs["policy"] = BehaviorPolicy.model_validate({**kwargs["policy"].model_dump(), "output": output})
    lifecycle = []

    @contextmanager
    def stream(query):
        assert query.sql.endswith("LIMIT 4") and query.max_rows == 4
        assert "SELECT *" not in query.sql
        assert "orders" not in repr(query)
        lifecycle.append("open")
        try:
            yield iter([pa.RecordBatch.from_pylist([row], schema=kwargs["schema"]) for row in [
                {"label": "alpha", "measured": 2}, {"label": "beta", "measured": 1}]])
        finally:
            lifecycle.append("closed")

    source = _capture_authorized_result(request, stream=stream, **kwargs)
    assert lifecycle == ["open", "closed"]
    profile = _profile_transformation_source(source, kwargs["policy"], budget=GenerationBudget(5), max_bytes=16384)
    policy = kwargs["policy"].model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    material = prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(), source, (),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_csv_publication(material, max_total_bytes=32768, max_review_bytes=8192,
            max_output_bytes=16384, budget=GenerationBudget(5)) as output:
        if output_format == "csv":
            assert list(csv.DictReader(io.StringIO((output / "dataset.csv").read_text()))) == [
                {"label": "gamma", "measured": "8"}, {"label": "delta", "measured": "7"}]
        elif output_format == "parquet":
            import pyarrow.parquet as pq
            assert pq.read_table(output / "dataset.parquet").to_pylist() == [
                {"label": "gamma", "measured": 8}, {"label": "delta", "measured": 7}]
        else:
            payload = (output / "dataset.sql").read_text()
            assert "VALUES ('gamma', 8);" in payload
            assert "VALUES ('delta', 7);" in payload
    assert not output.parent.exists()
    # Unused authorization context is still exact-byte bound, not discarded.
    changed = _capture_authorized_result(request, stream=stream, **{
        **kwargs, "allowed_tables": kwargs["allowed_tables"] | {"other.safe"}})
    assert source.payload != changed.payload


@pytest.mark.parametrize("fault", ["table", "column", "format", "schema", "sensitive", "bytes", "rows", "nested"])
def test_capture_preflight_never_opens_stream_on_invalid_input(tmp_path, fault):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    if fault == "table":
        kwargs["allowed_tables"] = frozenset({"public.other"})
    elif fault == "column":
        kwargs["source_columns"] = (QuerySourceColumn("other", "text", False),)
    elif fault == "format":
        kwargs["policy"] = kwargs["policy"].model_copy(update={"input_format": "parquet"})
    elif fault == "schema":
        kwargs["schema"] = pa.schema([("other", pa.string())])
    elif fault == "sensitive":
        kwargs["source_columns"] += (QuerySourceColumn("private_token", "text", True),)
    elif fault == "bytes":
        kwargs["max_bytes"] = 10
    elif fault == "rows":
        kwargs["max_rows"] = True
    elif fault == "nested":
        kwargs["schema"] = pa.schema([("label", pa.list_(pa.string())), ("measured", pa.int64())])

    def forbidden(query):
        pytest.fail("invalid preflight called stream")

    with pytest.raises(ValueError, match="^invalid bounded query capture$") as caught:
        _capture_authorized_result(request, stream=forbidden, **kwargs)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("fault", ["row_limit", "decoded_bytes", "schema_drift", "null", "backend", "deadline"])
def test_stream_failure_closes_without_snapshot(tmp_path, fault):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    closed = []
    clock = [0.0]
    kwargs["budget"] = GenerationBudget(5, clock=lambda: clock[0])
    kwargs["max_rows"] = 1

    @contextmanager
    def stream(query):
        def batches():
            if fault == "backend":
                raise RuntimeError("fictional-sensitive-backend-detail")
            if fault == "deadline":
                clock[0] = 10.0
            schema = kwargs["schema"]
            if fault == "schema_drift":
                schema = pa.schema([("label", pa.string()), ("measured", pa.float64())])
            value = None if fault == "null" else 2
            label = "x" * 20000 if fault == "decoded_bytes" else "alpha"
            yield pa.RecordBatch.from_pylist([{"label": label, "measured": value}], schema=schema)
            if fault == "row_limit":
                yield pa.RecordBatch.from_pylist([{"label": "beta", "measured": 1}], schema=schema)
        try:
            yield batches()
        finally:
            closed.append(True)

    with pytest.raises(ValueError, match="^invalid bounded query capture$") as caught:
        _capture_authorized_result(request, stream=stream, **kwargs)
    assert closed == [True]
    assert caught.value.__context__ is None
