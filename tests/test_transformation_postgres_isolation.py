"""Fictional process-isolation experiment, not a production transport adapter."""

import multiprocessing
import os
import time
from functools import partial

import pytest

pytest.importorskip("pyarrow")

from tests.test_transformation_query_capture import setup
from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.sql_query_source import SqlQueryAdapter


def _driver(fault, stage):
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
    "cursor_close", "connection_close", "error"])
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

    with pytest.raises(ValueError, match="^invalid isolated PostgreSQL capture$") as caught:
        _capture_postgres_isolated(capture, driver_factory=forbidden, max_seconds=seconds)
    assert caught.value.__context__ is None
