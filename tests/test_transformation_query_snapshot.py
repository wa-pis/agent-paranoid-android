"""Fictional closed snapshots; no database or provider calls."""

import io

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import EffectiveInputLimit, InputDimension, TransformationLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader
from test_data_agent.io.transformation_query_snapshot import _capture_query_result, _query_result_payload


@pytest.mark.parametrize("adapter", ["postgres_query", "trino_query"])
@pytest.mark.parametrize("fault", ["missing", "adapter", "digest", "version", "nested"])
def test_invalid_query_capture_rejected(adapter, fault):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    buffer = io.BytesIO()
    pq.write_table(pa.table({"code": [["fictional"]] if fault == "nested" else ["fictional"]}), buffer)
    source = _capture_query_result(buffer.getvalue(), adapter=adapter, query_sha256="a" * 64, entity="items")
    payload = source.payload
    if fault == "missing":
        payload = buffer.getvalue()
    elif fault == "adapter":
        payload = payload.replace(adapter.encode(), b"foreign_query", 1)
    elif fault == "digest":
        payload = payload.replace(b"a" * 64, b"not-a-digest", 1)
    elif fault == "version":
        payload = payload.replace(b"APA-QUERY-1", b"APA-QUERY-2", 1)
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "input_format": adapter, "fields": [
            {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
             "behavior": {"action": "drop"}}]})
    with pytest.raises(ValueError):
        source_reader(SnapshotPart("source", "items", payload), policy, budget=GenerationBudget(5))


def test_capture_keeps_bytes_and_rejects_bad_identity():
    source = _capture_query_result(b"typed-bytes", adapter="postgres_query", query_sha256="a" * 64, entity="items")
    assert _query_result_payload(source.payload, "postgres_query") == b"typed-bytes"
    assert "typed-bytes" not in repr(source)
    for digest in ("", "A" * 64, "a" * 63, "a" * 65, None):
        with pytest.raises(ValueError, match="invalid captured query result"):
            _capture_query_result(b"typed-bytes", adapter="postgres_query", query_sha256=digest, entity="items")


def test_capture_envelope_included_in_exact_byte_budget():
    arguments = dict(adapter="postgres_query", query_sha256="a" * 64, entity="items")
    source = _capture_query_result(b"typed-bytes", **arguments)
    size = len(source.payload)
    assert _capture_query_result(b"typed-bytes", **arguments,
        byte_limit=EffectiveInputLimit(InputDimension.BYTES, size, "profile")) == source
    with pytest.raises(TransformationLimitError) as caught:
        _capture_query_result(b"typed-bytes", **arguments,
            byte_limit=EffectiveInputLimit(InputDimension.BYTES, size - 1, "profile"))
    assert (caught.value.amount, caught.value.limit) == (size, size - 1)
