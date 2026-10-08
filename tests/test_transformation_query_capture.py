"""Fictional stream through authorization, snapshot review and temporary output."""

from contextlib import contextmanager
import io
import csv
from dataclasses import replace
from functools import partial

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
from test_data_agent.io.transformation_publish import temporary_csv_publication
from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest, QuerySourceColumn

pa = pytest.importorskip("pyarrow")


@pytest.mark.parametrize("fault", [None, "scope", "source", "connect", "execute", "fetch",
    "names", "coercion", "null", "extra", "deadline", "consumer", "cancel"])
def test_private_postgres_driver_capture(tmp_path, fault):
    from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
    from test_data_agent.postgres_config import PostgresConfig

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    config = PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"}))
    if fault == "scope":
        config = replace(config, allowed_columns=frozenset({"public.orders.other"}))
    if fault == "source":
        config = replace(config, source_id="other")
    events = []
    now = [0.0]

    class Driver:
        description = [("label",), ("measured",)]
        rows = [("alpha", 2), ("beta", 1)]

        def connect(self, **options):
            events.append("connect")
            assert options["host"] == "fictional.invalid"
            assert "default_transaction_read_only=on" in options["options"]
            assert "statement_timeout=30000" in options["options"]
            assert "lock_timeout=5000" in options["options"]
            assert "idle_in_transaction_session_timeout=30000" in options["options"]
            if fault == "connect":
                raise RuntimeError("fictional backend detail")
            return self

        def cursor(self, **options):
            events.append("cursor")
            assert options == dict(name="apa_transform", scrollable=False, withhold=False)
            return self

        def execute(self, sql):
            events.append("execute")
            assert sql.endswith("LIMIT 4") and "COUNT(*)" in sql
            if fault == "execute":
                raise RuntimeError("fictional backend detail")

        def fetchmany(self, size):
            assert size == 1
            events.append("fetch")
            if fault == "fetch":
                raise RuntimeError("fictional backend detail")
            if fault == "cancel":
                raise KeyboardInterrupt
            if fault == "deadline":
                now[0] = 121.0
            if fault == "names":
                self.description = [("other",), ("measured",)]
            if fault == "coercion":
                return [("alpha", 2.5)]
            if fault == "null":
                return [("alpha", None)]
            if fault == "extra":
                return [("alpha", 2), ("beta", 1)]
            return [self.rows.pop(0)] if self.rows else []

        def rollback(self):
            events.append("rollback")

        def close(self):
            events.append("close")

    stream = partial(_postgres_result_stream, config=config, schema=kwargs["schema"],
        driver=Driver(), getenv=lambda name: None, clock=lambda: now[0])
    if fault == "consumer":
        original_stream = stream

        @contextmanager
        def stream(query):
            with original_stream(query) as batches:
                yield iter([next(batches), "invalid batch"])

    if fault is None:
        source = _capture_authorized_result(request, stream=stream, **kwargs)
        profile = _profile_transformation_source(source, kwargs["policy"],
            budget=GenerationBudget(5), max_bytes=16384)
        assert profile.source_type == "postgres_query"
    else:
        expected = KeyboardInterrupt if fault == "cancel" else ValueError
        with pytest.raises(expected) as caught:
            _capture_authorized_result(request, stream=stream, **kwargs)
        if fault != "cancel":
            assert str(caught.value) == "invalid bounded query capture"
            assert caught.value.__context__ is None
    if fault in {"scope", "source"}:
        assert events == []
    elif fault == "connect":
        assert events == ["connect"]
    else:
        assert events[-3:] == ["close", "rollback", "close"]


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

    expected = "limit_exceeded" if fault == "bytes" else "^invalid bounded query capture$"
    with pytest.raises(ValueError, match=expected) as caught:
        _capture_authorized_result(request, stream=forbidden, **kwargs)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("fault", ["row_limit", "decoded_bytes", "schema_drift", "null", "backend", "deadline"])
def test_stream_failure_closes_without_snapshot(tmp_path, fault):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    closed = []
    clock = [0.0]
    kwargs["budget"] = GenerationBudget(5, clock=lambda: clock[0])
    kwargs["max_rows"] = 1
    if fault == "decoded_bytes":
        kwargs["policy"] = BehaviorPolicy.model_validate({**kwargs["policy"].model_dump(),
            "resource_limits": {"max_parquet_expanded_bytes": 16384}})

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

    expected = "limit_exceeded" if fault in {"row_limit", "decoded_bytes"} else "^invalid bounded query capture$"
    with pytest.raises(ValueError, match=expected) as caught:
        _capture_authorized_result(request, stream=stream, **kwargs)
    assert closed == [True]
    assert caught.value.__context__ is None


def test_query_requested_limit_fails_before_stream_and_session_recovers(tmp_path, monkeypatch):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    kwargs["policy"] = BehaviorPolicy.model_validate({**kwargs["policy"].model_dump(),
        "resource_limits": {"max_input_rows": 2}})
    opened = []

    @contextmanager
    def stream(query):
        opened.append(True)
        yield iter(())

    with pytest.raises(TransformationLimitError) as caught:
        _capture_authorized_result(request, stream=stream, **kwargs)
    assert not opened
    assert (caught.value.code, caught.value.amount, caught.value.limit, caught.value.origin) == (
        "requested_above_limit", 3, 2, "profile")
    monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS", "3")
    assert _capture_authorized_result(request, stream=stream, **kwargs).kind == "source"
    assert opened == [True]


@pytest.mark.parametrize("key,threshold,amount", [
    ("max_input_columns", 1, 2), ("max_input_cells", 3, 4),
])
def test_query_dimensions_fail_closed_and_profile_recovers(tmp_path, key, threshold, amount):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    opened = []

    @contextmanager
    def stream(query):
        opened.append(True)
        yield iter([pa.RecordBatch.from_pylist([
            {"label": "alpha", "measured": 2}, {"label": "beta", "measured": 1}], schema=kwargs["schema"])])

    for limit in (threshold, amount):
        kwargs["policy"] = BehaviorPolicy.model_validate({**kwargs["policy"].model_dump(),
            "resource_limits": {key: limit}})
        if limit == threshold:
            with pytest.raises(TransformationLimitError) as caught:
                _capture_authorized_result(request, stream=stream, **kwargs)
            assert (caught.value.dimension.value, caught.value.amount, caught.value.limit) == (key, amount, threshold)
            assert caught.value.origin == "profile"
            assert caught.value.code == ("requested_above_limit" if key == "max_input_columns" else "limit_exceeded")
            if key == "max_input_columns":
                assert not opened
        else:
            assert _capture_authorized_result(request, stream=stream, **kwargs).kind == "source"


@pytest.mark.parametrize("invalid_tail", [False, True])
def test_postgres_batching_preserves_order_and_rejects_invalid_tail(tmp_path, invalid_tail):
    from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
    from test_data_agent.io.transformation_input import source_reader
    from test_data_agent.io.transformation_query_snapshot import _query_result_payload
    from test_data_agent.postgres_config import PostgresConfig
    import pyarrow.parquet as pq

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    kwargs.update(max_rows=2049, max_bytes=1024 * 1024)
    config = PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}), allowed_columns=frozenset({"public.orders.status"}))
    events = []

    class Driver:
        description = [("label",), ("measured",)]
        index = 0

        def connect(self, **options):
            return self

        def cursor(self, **options):
            return self

        def execute(self, sql):
            assert sql.endswith("LIMIT 2050")

        def fetchmany(self, size):
            assert size == 1
            if self.index == 2049:
                return []
            self.index += 1
            return [("alpha", True if invalid_tail and self.index == 2049 else self.index)]

        def rollback(self):
            events.append("rollback")

        def close(self):
            events.append("close")

    stream = partial(_postgres_result_stream, config=config, schema=kwargs["schema"],
        driver=Driver(), getenv=lambda _: None, clock=lambda: 0.0)
    if invalid_tail:
        with pytest.raises(ValueError, match="^invalid bounded query capture$"):
            _capture_authorized_result(request, stream=stream, **kwargs)
    else:
        source = _capture_authorized_result(request, stream=stream, **kwargs)
        assert [row["measured"] for row in source_reader(source, kwargs["policy"],
            budget=GenerationBudget(5))] == list(range(1, 2050))
        parquet = pq.ParquetFile(io.BytesIO(_query_result_payload(source.payload, "postgres_query")))
        assert parquet.metadata.num_row_groups == 3
    assert events == ["close", "rollback", "close"]


def test_capture_rejects_query_change_after_metadata_before_stream(tmp_path):
    from test_data_agent.sql_query_source import inspect_query_source, authorize_query_source

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    plan = authorize_query_source(inspect_query_source(request), kwargs["source_columns"])
    request.query_file.write_text("SELECT status AS label, COUNT(*) AS measured FROM public.orders "
        "WHERE status = 'fictional' GROUP BY status")

    def forbidden(query):
        pytest.fail("changed query must not open result stream")

    with pytest.raises(ValueError, match="invalid bounded query capture") as caught:
        _capture_authorized_result(request, stream=forbidden,
            expected_query_sha256=plan.fingerprint, **kwargs)
    assert caught.value.__context__ is None


def test_utc_timestamp_capture_replacement_keeps_microseconds(tmp_path):
    from datetime import datetime, timezone

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    original = "2024-01-02T03:04:05.123456+00:00"
    replacement = "2030-02-03T04:05:06.654321+00:00"
    declaration = kwargs["policy"].model_dump(mode="json")
    declaration["fields"][0]["behavior"]["mapping"]["entries"] = [
        {"original": [original], "replacement": [replacement]}]
    kwargs["policy"] = BehaviorPolicy.model_validate(declaration)
    kwargs["schema"] = pa.schema([pa.field("label", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("measured", pa.int64(), nullable=False)])

    @contextmanager
    def stream(query):
        yield iter([pa.RecordBatch.from_pylist([
            {"label": datetime(2024, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc), "measured": 2}],
            schema=kwargs["schema"])])

    source = _capture_authorized_result(request, stream=stream, **kwargs)
    profile = _profile_transformation_source(source, kwargs["policy"],
        budget=GenerationBudget(5), max_bytes=16384)
    policy = kwargs["policy"].model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    material = prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(), source, (),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_csv_publication(material, max_total_bytes=32768, max_review_bytes=8192,
            max_output_bytes=16384, budget=GenerationBudget(5)) as output:
        assert list(csv.DictReader(io.StringIO((output / "dataset.csv").read_text()))) == [
            {"label": replacement, "measured": "8"}]


def test_timestamp_reuse_guard_compares_instants_without_string_coercion():
    from datetime import datetime, timezone
    from test_data_agent.io.transformation_input import same_native_value

    original = datetime(2024, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
    assert same_native_value(original, "2024-01-02T04:04:05.123456+01:00")
    assert not same_native_value(original, "2024-01-02T03:04:05.123456")
    assert not same_native_value(original, "fictional malformed timestamp")


@pytest.mark.parametrize("fault", [None, "scope", "names", "native"])
def test_closed_trino_driver_capture_obeys_scope_and_native_types(tmp_path, fault):
    from test_data_agent.io.transformation_trino_stream import _trino_result_stream
    from tests.test_trino_client import FakeCursor, FakeDriver, client_config

    request, kwargs = setup(tmp_path, SqlQueryAdapter.TRINO)
    config = replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.other" if fault == "scope"
            else "lake.safe.orders.status"}))
    cursor = FakeCursor([("alpha", 2.5 if fault == "native" else 2), ("beta", 1)])
    cursor.description = [("other" if fault == "names" else "label",), ("measured",)]
    driver = FakeDriver(cursor)
    stream = partial(_trino_result_stream, config=config, source_id="warehouse",
        schema=kwargs["schema"], driver=driver)
    if fault is None:
        source = _capture_authorized_result(request, stream=stream, **kwargs)
        assert source.kind == "source"
    else:
        with pytest.raises(ValueError, match="invalid bounded query capture"):
            _capture_authorized_result(request, stream=stream, **kwargs)
    if fault == "scope":
        assert driver.dbapi.connect_kwargs is None
    else:
        assert cursor.closed and driver.dbapi.connection.closed


@pytest.mark.parametrize("fault", [None, "source", "scope", "names"])
def test_trino_capture_metadata_is_allowlisted_and_contains_no_rows(tmp_path, fault):
    from test_data_agent.io.transformation_trino_stream import _discover_trino_capture_metadata
    from tests.test_trino_client import FakeCursor, FakeDriver, client_config

    request, _ = setup(tmp_path, SqlQueryAdapter.TRINO)
    config = replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.status"}))
    if fault == "scope":
        config = replace(config, allowed_catalogs=frozenset({"other"}))

    class Cursor(FakeCursor):
        def execute(self, sql, parameters):
            self.row_offset = 0
            if "information_schema.columns" in sql:
                self.rows = [("status", "varchar", "NO")]
                self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
            else:
                assert sql.endswith("WHERE FALSE")
                self.rows = []
                self.description = [("other" if fault == "names" else "label", "varchar"),
                    ("measured", "bigint")]

    cursor = Cursor([])
    driver = FakeDriver(cursor)
    if fault is None:
        columns, metadata, plan = _discover_trino_capture_metadata(request,
            config=config, source_id="warehouse", driver=driver)
        assert columns[0].name == "status"
        assert tuple(item.name for item in metadata) == plan.output_fields
    else:
        with pytest.raises(ValueError, match="invalid Trino capture metadata"):
            _discover_trino_capture_metadata(request, config=config,
                source_id="other" if fault == "source" else "warehouse", driver=driver)
    if fault in {"source", "scope"}:
        assert driver.dbapi.connect_kwargs is None
    else:
        assert cursor.closed and driver.dbapi.connection.closed


@pytest.mark.parametrize("kind", ["array(varchar)", "decimal(39,2)", "decimal(8,9)",
    "timestamp(9) with time zone", "varchar(999)", "varbinary"])
def test_trino_capture_schema_rejects_unsupported_declarations(kind):
    from test_data_agent.io.transformation_trino_stream import _trino_capture_schema
    from test_data_agent.sql_query_profiling import QueryResultColumn

    with pytest.raises(ValueError, match="unsupported Trino capture schema") as error:
        _trino_capture_schema((QueryResultColumn("fictional", kind),))
    assert error.value.__cause__ is None
    assert kind not in str(error.value)


def test_trino_capture_schema_retains_exact_decimal_and_integer_width():
    from test_data_agent.io.transformation_trino_stream import _trino_capture_schema
    from test_data_agent.sql_query_profiling import QueryResultColumn

    schema = _trino_capture_schema((QueryResultColumn("amount", "decimal(38,6)", False),
        QueryResultColumn("count", "tinyint", True)))
    assert schema == pa.schema([pa.field("amount", pa.decimal128(38, 6), nullable=False),
        pa.field("count", pa.int8(), nullable=True)])


@pytest.mark.parametrize("statements", [2, 3])
def test_composed_trino_capture_keeps_one_statement_budget(tmp_path, monkeypatch, statements):
    from test_data_agent.io.transformation_trino_stream import _capture_trino_result
    from tests.test_trino_client import FakeCursor, FakeDriver, client_config

    monkeypatch.setenv("TRINO_MAX_INVOCATION_STATEMENTS", str(statements))
    request, kwargs = setup(tmp_path, SqlQueryAdapter.TRINO)
    config = replace(client_config(max_result_rows=4), allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.*"}))

    class Cursor(FakeCursor):
        def execute(self, sql, parameters):
            self.row_offset = 0
            if "information_schema.columns" in sql:
                self.rows = [("status", "varchar", "NO")]
                self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
            else:
                self.rows = [] if sql.endswith("WHERE FALSE") else [("alpha", 2), ("beta", 1)]
                self.description = [("label", "varchar"), ("measured", "bigint")]

    cursor = Cursor([])
    driver = FakeDriver(cursor)
    arguments = dict(config=config, source_id="warehouse", policy=kwargs["policy"],
        max_rows=3, max_bytes=16384, budget=GenerationBudget(5), driver=driver)
    if statements == 3:
        source = _capture_trino_result(request, **arguments)
        assert source.payload
    else:
        with pytest.raises(ValueError):
            _capture_trino_result(request, **arguments)
    assert cursor.closed and driver.dbapi.connection.closed
