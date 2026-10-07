"""Fictional process-isolation experiment, not a production transport adapter."""

import multiprocessing
import os
import signal
import time
import csv
import yaml
from functools import partial

import pytest

pytest.importorskip("pyarrow")

from tests.test_transformation_query_capture import setup
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.sql_query_source import SqlQueryAdapter


def _driver(fault, stage):
    if fault == "ignore_term":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        fault = "fetch"
    def step(name):
        if fault == name:
            stage.value = 1
            while True:
                time.sleep(1)

    class FictionalDriver:
        description = [("label",), ("measured",)]

        def __init__(self):
            self.rows = [("alpha", 2), ("beta", 1)]
            self.closes = 0

        def connect(self, **options):
            os.write(2, b"fictional driver diagnostic must not escape\n")
            step("connect")
            if fault == "error":
                raise RuntimeError("fictional backend detail")
            return self

        def cursor(self, **options):
            return self

        def execute(self, sql):
            step("execute")

        def fetchmany(self, size):
            step("fetch")
            return [self.rows.pop(0)] if self.rows else []

        def rollback(self):
            step("rollback")

        def close(self):
            self.closes += 1
            step("cursor_close" if self.closes == 1 else "connection_close")

    return FictionalDriver()


def _config():
    return PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"}))


def _worker(request, kwargs, fault, result, length, stage):
    # Discard native fd writes as well as Python logging before touching driver.
    with open(os.devnull, "wb") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)

    try:
        source = _capture_authorized_result(request, stream=partial(_postgres_result_stream,
            config=_config(), schema=kwargs["schema"], driver=_driver(fault, stage),
            getenv=lambda name: None, clock=time.monotonic), **kwargs)
        payload = source.payload
        if len(payload) > len(result):
            length.value = -1
            return
        if fault == "partial":
            result[:8] = payload[:8]
            stage.value = 1
            while True:
                time.sleep(1)
        result[:len(payload)] = payload
        # Parent accepts only after successful process exit, never this flag alone.
        length.value = len(payload)
    except BaseException:
        length.value = -1


@pytest.mark.parametrize("fault", [None, "connect", "execute", "fetch", "rollback",
    "cursor_close", "connection_close", "partial", "error", "oversize", "cancel"])
def test_isolated_fictional_capture_is_reaped_and_never_returns_partial(tmp_path, capfd, fault):
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    # Spawn avoids inheriting a parent's active database connection or threads.
    context = multiprocessing.get_context("spawn")
    result = context.RawArray("B", 8 if fault == "oversize" else kwargs["max_bytes"])
    length = context.RawValue("i", 0)
    stage = context.RawValue("i", 0)
    process = context.Process(target=_worker, args=(request, kwargs,
        "fetch" if fault == "cancel" else fault, result, length, stage))
    blocked = fault in {"connect", "execute", "fetch", "rollback", "cursor_close",
        "connection_close", "partial", "cancel"}
    accepted = None
    process.start()
    try:
        if blocked:
            # Separate bounded startup allowance from the deliberately blocked call.
            ready_deadline = time.monotonic() + 10
            while stage.value != 1 and process.is_alive() and time.monotonic() < ready_deadline:
                time.sleep(0.01)
            assert stage.value == 1, "fictional worker never reached requested stage"
            if fault == "cancel":
                raise KeyboardInterrupt
            process.join(0.15)
            assert process.is_alive(), "fixture did not remain blocked"
        else:
            process.join(10)
            assert not process.is_alive(), "fictional capture exceeded deadline"
            if process.exitcode == 0 and 0 < length.value <= len(result):
                accepted = bytes(result[:length.value])
    except KeyboardInterrupt:
        assert fault == "cancel"
    finally:
        if process.is_alive():
            process.terminate()
            process.join(1)
        if process.is_alive():
            process.kill()
            process.join(1)
        assert not process.is_alive(), "worker could not be reaped"
        process.close()
    if fault is None:
        assert accepted is not None and accepted.startswith(b"APA-QUERY-1\npostgres_query\n")
    else:
        assert accepted is None
    assert "fictional driver diagnostic" not in capfd.readouterr().err


@pytest.mark.parametrize("fault", [None, "connect", "execute", "fetch", "rollback",
    "cursor_close", "connection_close", "error",
    pytest.param("ignore_term", marks=pytest.mark.skipif(os.name != "posix",
        reason="SIGTERM-ignore evidence is POSIX-specific"))])
def test_private_supervisor_uses_actual_capture(tmp_path, capfd, fault):
    from test_data_agent.io.transformation_postgres_capture import (
        _PostgresCapture, _capture_postgres_isolated,
    )
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    capture = _PostgresCapture(request=request, config=_config(), **{
        key: value for key, value in kwargs.items() if key not in {"allowed_tables", "budget"}})
    stage = multiprocessing.get_context("spawn").RawValue("i", 0)
    previous = {child.pid for child in multiprocessing.active_children()}
    start = time.monotonic()
    if fault is None:
        source = _capture_postgres_isolated(capture, driver_factory=partial(_driver, fault, stage),
            max_seconds=4)
        assert source.kind == "source" and source.name == request.entity_name
        assert source.payload.startswith(b"APA-QUERY-1\npostgres_query\n")
    else:
        with pytest.raises(ValueError, match="^invalid isolated PostgreSQL capture$") as caught:
            _capture_postgres_isolated(capture, driver_factory=partial(_driver, fault, stage),
                max_seconds=4)
        assert caught.value.__context__ is None
        if fault != "error":
            assert stage.value == 1
    assert time.monotonic() - start < 5
    assert {child.pid for child in multiprocessing.active_children()} == previous
    assert "fictional driver diagnostic" not in capfd.readouterr().err


@pytest.mark.parametrize("seconds,byte_limit", [(True, 100), (float("nan"), 100),
    (0, 100), (5, True), (5, 0), (5, 1_000_000_000)])
def test_private_supervisor_rejects_unbounded_controls(tmp_path, seconds, byte_limit):
    from test_data_agent.io.transformation_postgres_capture import (
        _PostgresCapture, _capture_postgres_isolated,
    )
    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    kwargs["max_bytes"] = byte_limit
    capture = _PostgresCapture(request=request, config=_config(), **{
        key: value for key, value in kwargs.items() if key not in {"allowed_tables", "budget"}})

    def forbidden():
        pytest.fail("invalid controls opened driver")

    expected = "requested_above_limit" if byte_limit == 1_000_000_000 else "^invalid isolated PostgreSQL capture$"
    with pytest.raises(ValueError, match=expected) as caught:
        _capture_postgres_isolated(capture, driver_factory=forbidden, max_seconds=seconds)
    assert caught.value.__context__ is None


def test_isolated_limit_diagnostic_and_session_recovery(tmp_path, monkeypatch, capfd):
    from test_data_agent.io.transformation_postgres_capture import _PostgresCapture, _capture_postgres_isolated
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
    from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
    from test_data_agent.io.transformation_publish import temporary_csv_publication

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    kwargs["max_rows"] = 10001  # Above profiling defaults; no profiling setting is raised.
    kwargs["policy"] = BehaviorPolicy.model_validate({**kwargs["policy"].model_dump(),
        "resource_limits": {"max_input_cell_chars": 4}})
    capture = _PostgresCapture(request=request, config=_config(), **{
        key: value for key, value in kwargs.items() if key not in {"allowed_tables", "budget"}})
    stage = multiprocessing.get_context("spawn").RawValue("i", 0)
    previous = {child.pid for child in multiprocessing.active_children()}
    with pytest.raises(TransformationLimitError) as caught:
        _capture_postgres_isolated(capture, driver_factory=partial(_driver, None, stage), max_seconds=5)
    error = caught.value
    assert (error.amount, error.limit, error.origin, error.code) == (5, 4, "profile", "limit_exceeded")
    assert error.dimension.value == "max_input_cell_chars"
    assert "TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_CELL_CHARS" in str(error)
    assert "resource_limits.max_input_cell_chars" in str(error)
    assert "alpha" not in str(error) and error.__context__ is None
    monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_CELL_CHARS", "5")
    source = _capture_postgres_isolated(capture, driver_factory=partial(_driver, None, stage), max_seconds=5)
    assert source.payload.startswith(b"APA-QUERY-1\npostgres_query\n")
    profile = _profile_transformation_source(source, capture.policy, budget=GenerationBudget(5), max_bytes=16384)
    policy = capture.policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    material = prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(), source, (),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_csv_publication(material, max_total_bytes=32768, max_review_bytes=8192,
            max_output_bytes=16384, budget=GenerationBudget(5)) as output:
        with (output / "dataset.csv").open() as handle:
            assert list(csv.DictReader(handle)) == [
                {"label": "gamma", "measured": "8"}, {"label": "delta", "measured": "7"}]
    assert not output.parent.exists()
    assert {child.pid for child in multiprocessing.active_children()} == previous
    assert "fictional driver diagnostic" not in capfd.readouterr().err


def _cancellation_driver(stage, worker_pid):
    worker_pid.value = os.getpid()
    return _driver("fetch", stage)


def _cancelled_supervisor(capture, stage, worker_pid, outcome):
    from test_data_agent.io.transformation_postgres_capture import _capture_postgres_isolated

    # Signal only this isolated harness, never pytest or the user's terminal.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        _capture_postgres_isolated(capture,
            driver_factory=partial(_cancellation_driver, stage, worker_pid), max_seconds=10)
        outcome.value = 2
    except KeyboardInterrupt:
        outcome.value = 1 if not multiprocessing.active_children() else -1
    except BaseException:
        outcome.value = -2
    finally:
        for child in multiprocessing.active_children():
            child.terminate()
            child.join(1)
            if child.is_alive():
                child.kill()
                child.join(1)


@pytest.mark.skipif(os.name != "posix", reason="isolated SIGINT evidence is POSIX-specific")
def test_actual_supervisor_caller_cancellation_reaps_worker(tmp_path):
    from test_data_agent.io.transformation_postgres_capture import _PostgresCapture

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    capture = _PostgresCapture(request=request, config=_config(), **{
        key: value for key, value in kwargs.items() if key not in {"allowed_tables", "budget"}})
    context = multiprocessing.get_context("spawn")
    stage = context.RawValue("i", 0)
    worker_pid = context.RawValue("i", 0)
    outcome = context.RawValue("i", 0)
    harness = context.Process(target=_cancelled_supervisor,
        args=(capture, stage, worker_pid, outcome))
    harness.start()
    try:
        deadline = time.monotonic() + 8
        while stage.value != 1 and harness.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert stage.value == 1 and worker_pid.value > 0
        os.kill(harness.pid, signal.SIGINT)
        harness.join(4)
        assert not harness.is_alive() and harness.exitcode == 0
        assert outcome.value == 1, "cancellation returned output or left worker alive"
        with pytest.raises(ProcessLookupError):
            os.kill(worker_pid.value, 0)
    finally:
        if harness.is_alive():
            # Give the harness's own ten-second deadline/cleanup a chance to run.
            harness.join(12)
        if harness.is_alive():
            harness.kill()
            harness.join(1)
        harness.close()


def test_configured_capture_rejects_invalid_request_before_driver_resolution(monkeypatch):
    from test_data_agent.io import transformation_postgres_capture as module

    def forbidden():
        pytest.fail("invalid capture must not load or connect a driver")

    monkeypatch.setattr(module, "_configured_postgres_driver", forbidden)
    with pytest.raises(ValueError, match="invalid isolated PostgreSQL capture"):
        module._capture_configured_postgres(object(), max_seconds=5)


@pytest.mark.parametrize("fault", ["source", "table", "adapter"])
def test_capture_metadata_rejects_unauthorized_request_before_connection(tmp_path, fault):
    from dataclasses import replace
    from test_data_agent.io.transformation_postgres_capture import _discover_postgres_capture_metadata
    from test_data_agent.postgres_config import PostgresConfig
    from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest

    query = tmp_path / "query.sql"
    query.write_text("SELECT status FROM public.orders")
    request = SqlQueryProfileRequest(SqlQueryAdapter.POSTGRES, "warehouse", "orders", query)
    config = PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"}))
    if fault == "source":
        request = replace(request, source_id="other")
    elif fault == "table":
        config = replace(config, allowed_tables=frozenset({"public.other"}),
            allowed_columns=frozenset({"public.other.status"}))
    else:
        request = replace(request, adapter=SqlQueryAdapter.TRINO)

    class ForbiddenDriver:
        def connect(self, **kwargs):
            pytest.fail("unauthorized metadata must not connect")

    with pytest.raises(ValueError, match="invalid PostgreSQL capture metadata") as caught:
        _discover_postgres_capture_metadata(request, config, driver=ForbiddenDriver())
    assert caught.value.__context__ is None


@pytest.mark.parametrize("drift", [False, True])
def test_capture_metadata_uses_only_authorized_no_row_schema(tmp_path, monkeypatch, drift):
    from test_data_agent.io.transformation_postgres_capture import _discover_postgres_capture_metadata
    from test_data_agent import postgres_client
    from test_data_agent.postgres_config import PostgresConfig
    from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest

    query = tmp_path / "query.sql"
    query.write_text("SELECT status AS label FROM public.orders")
    request = SqlQueryProfileRequest(SqlQueryAdapter.POSTGRES, "warehouse", "orders", query)
    config = PostgresConfig(source_id="warehouse", host="fictional.invalid", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"}))
    events = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            events.append("closed")

        def fetch_aggregate_dicts(self, query):
            assert "pg_catalog.pg_attribute" in query.sql
            return [{"column_name": "status", "data_type": "text", "is_nullable": True}]

        def describe_no_rows(self, query):
            assert query.sql.endswith("WHERE FALSE")
            assert '"label"' in query.sql
            return (postgres_client.PostgresResultColumn(
                "other" if drift else "label", "text", True),)

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["config"] is config

        def session(self):
            return Session()

    monkeypatch.setattr(postgres_client, "PostgresClient", Client)
    if drift:
        with pytest.raises(ValueError, match="invalid PostgreSQL capture metadata"):
            _discover_postgres_capture_metadata(request, config, driver=object())
    else:
        columns, result = _discover_postgres_capture_metadata(request, config, driver=object())
        assert columns[0].name == "status" and result[0].name == "label"
    assert events == ["closed"]


@pytest.mark.parametrize("kind", ["numeric", "numeric(39,2)", "numeric(4,5)",
    "numeric(8,-2)", "jsonb", "integer[]", "timestamp without time zone"])
def test_capture_schema_refuses_lossy_or_unsupported_metadata(kind):
    from test_data_agent.io.transformation_postgres_capture import _postgres_capture_schema
    from test_data_agent.postgres_client import PostgresResultColumn

    with pytest.raises(ValueError, match="unsupported PostgreSQL capture schema") as caught:
        _postgres_capture_schema((PostgresResultColumn("value", kind, True),))
    assert caught.value.__context__ is None


def test_capture_schema_preserves_exact_decimal_width_and_nullability():
    import pyarrow as pa
    from test_data_agent.io.transformation_postgres_capture import _postgres_capture_schema
    from test_data_agent.postgres_client import PostgresResultColumn

    schema = _postgres_capture_schema((PostgresResultColumn("amount", "numeric(38, 6)", False),
        PostgresResultColumn("count", "integer", True)))
    assert schema.field("amount").type == pa.decimal128(38, 6)
    assert schema.field("amount").nullable is False
    assert schema.field("count").type == pa.int32()
    assert schema.field("count").nullable is True


def _metadata_driver(fault=None):
    from types import SimpleNamespace

    class Cursor:
        def execute(self, sql, parameters=()):
            self.metadata = "pg_catalog.pg_attribute" in sql
            if self.metadata:
                self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
                self.rows = [("status", "text", True)]
            else:
                self.description = [("other" if fault == "schema_drift" else "label",
                    SimpleNamespace(name="text"), None, None, None, None, True)]
                self.rows = [] if sql.endswith("WHERE FALSE") else [("alpha",), ("beta",)]

        def fetchmany(self, size):
            assert size == 1
            if self.metadata and fault == "metadata_fetch":
                while True:
                    time.sleep(1)
            return [self.rows.pop(0)] if self.rows else []

        def close(self):
            pass

    class Driver:
        def connect(self, **kwargs):
            assert "default_transaction_read_only=on" in kwargs["options"]
            return self

        def cursor(self, **kwargs):
            return Cursor()

        def rollback(self):
            pass

        def close(self):
            pass

    return Driver()


def test_owned_worker_discovers_metadata_before_result_capture(tmp_path):
    from test_data_agent.io.transformation_postgres_capture import _PostgresCapture, _capture_postgres_isolated
    from test_data_agent.io.transformation_source import _profile_transformation_source
    from test_data_agent.core.limits import GenerationBudget

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    request.query_file.write_text("SELECT status AS label FROM public.orders")
    policy = kwargs["policy"].model_copy(update={"fields": kwargs["policy"].fields[:1]})
    capture = _PostgresCapture(request, _config(), (), None, policy, 3, 16384)
    source = _capture_postgres_isolated(capture, driver_factory=_metadata_driver, max_seconds=10)
    profile = _profile_transformation_source(source, policy, budget=GenerationBudget(5), max_bytes=16384)
    assert profile.source_type == "postgres_query"


@pytest.mark.parametrize("fault", ["metadata_fetch", "schema_drift"])
def test_owned_metadata_failure_returns_no_snapshot_and_reaps_worker(tmp_path, fault):
    from test_data_agent.io.transformation_postgres_capture import _PostgresCapture, _capture_postgres_isolated

    request, kwargs = setup(tmp_path, SqlQueryAdapter.POSTGRES)
    request.query_file.write_text("SELECT status AS label FROM public.orders")
    policy = kwargs["policy"].model_copy(update={"fields": kwargs["policy"].fields[:1]})
    capture = _PostgresCapture(request, _config(), (), None, policy, 3, 16384)
    before = {child.pid for child in multiprocessing.active_children()}
    with pytest.raises(ValueError, match="invalid isolated PostgreSQL capture"):
        _capture_postgres_isolated(capture, driver_factory=partial(_metadata_driver, fault),
            max_seconds=2)
    assert {child.pid for child in multiprocessing.active_children()} == before
