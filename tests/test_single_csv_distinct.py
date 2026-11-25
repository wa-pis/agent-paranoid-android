"""Single-file CSV counting shares exact, bounded, digest-only folder behavior."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

import pytest

import test_data_agent.csv_profiler as single
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.profiling import duckdb_distinct


def _payload() -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["record_id", "stock_code", "measure"])
    for index in range(48):
        writer.writerow([
            index % 17,
            "4242" * 4 if index == 40 else f"synthetic_stock_{index % 11}",
            "" if index % 5 == 0 else f"-{index + 1}.25",
        ])
    return stream.getvalue().encode()


@pytest.mark.parametrize("entrypoint", ["file", "snapshot", "digests"])
def test_single_csv_handoff_preserves_full_profile_without_reopening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    path = tmp_path / "records.csv"
    payload = _payload()
    path.write_bytes(payload)

    def run() -> Any:
        if entrypoint == "snapshot":
            return single.profile_csv_bytes(payload, "records", budget=GenerationBudget())
        if entrypoint == "digests":
            return single.profile_csv_with_row_digests(path)
        return single.profile_csv(path)

    expected = run()
    calls = []

    def count(initial: list[set[bytes]], remaining: Any, budget: Any) -> list[int]:
        # The source has already been opened. Continuation must use that iterator.
        path.unlink()
        budget.check_deadline("test distinct handoff")
        for column, digest in remaining:
            assert type(column) is int
            assert type(digest) is bytes and len(digest) == 32
            initial[column].add(digest)
        calls.append([len(values) for values in initial])
        return calls[-1]

    monkeypatch.setattr(single, "MAX_IN_MEMORY_DISTINCT", 4)
    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", count)
    actual = run()

    assert actual == expected
    assert calls == [[17, 12, 38]]
    profile = actual[0] if entrypoint == "digests" else actual
    assert all(column.unique_ratio_kind == "exact" for column in profile.columns)
    assert profile.columns[1].sensitive and profile.columns[1].semantic_type is None
    assert "4242" * 4 not in profile.model_dump_json()
    normalized = csv_profile_to_dataset_profile(profile)
    assert normalized.entity("records").field("record_id").distribution["pool_size"] == 17


def test_single_csv_real_duckdb_matches_set_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    path = tmp_path / "records.csv"
    path.write_bytes(_payload())
    expected = single.profile_csv_with_row_digests(path)

    monkeypatch.setattr(single, "MAX_IN_MEMORY_DISTINCT", 4)
    assert single.profile_csv_with_row_digests(path) == expected


def test_snapshot_handoff_preserves_generation_budget_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    generation = GenerationBudget(max_seconds=10.0, clock=lambda: 0.0)
    real_count = duckdb_distinct.count_distinct_stream

    def expired(stage: str) -> None:
        raise GenerationLimitError("generation exceeded its synthetic test budget")

    def count(initial: list[set[bytes]], remaining: Any, budget: Any) -> list[int]:
        monkeypatch.setattr(generation, "check", expired)
        return real_count(initial, remaining, budget)

    monkeypatch.setattr(single, "MAX_IN_MEMORY_DISTINCT", 4)
    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", count)
    with pytest.raises(GenerationLimitError, match="^generation exceeded its synthetic test budget$"):
        single.profile_csv_bytes(_payload(), "records", budget=generation)


def test_single_csv_accumulator_has_no_distinct_ceiling() -> None:
    accumulator = single.CSVColumnAccumulator("record_id")
    for index in range(100_001):
        accumulator.add_count(str(index))
    assert len(accumulator.distinct_digests) == 100_001
    assert all(type(value) is bytes and len(value) == 32 for value in accumulator.distinct_digests)


def test_single_csv_backend_failure_does_not_return_partial_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "records.csv"
    path.write_bytes(_payload())

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise duckdb_distinct.DistinctTrackingError("local distinct counting or scratch cleanup failed")

    monkeypatch.setattr(single, "MAX_IN_MEMORY_DISTINCT", 4)
    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", fail)
    with pytest.raises(duckdb_distinct.DistinctTrackingError, match="^local distinct counting"):
        single.profile_csv(path)
    assert list(tmp_path.iterdir()) == [path]


def test_generation_remaining_budget_is_bounded_and_expires() -> None:
    now = [0.0]
    budget = GenerationBudget(max_seconds=1.0, clock=lambda: now[0])
    now[0] = 0.25
    assert budget.remaining_seconds() == 0.75
    now[0] = 1.0
    with pytest.raises(GenerationLimitError, match="native work configuration"):
        budget.remaining_seconds()


def test_snapshot_native_budget_uses_remaining_generation_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = []

    def count(initial: list[set[bytes]], remaining: Any, budget: Any) -> list[int]:
        seen.append(budget.limits.max_seconds)
        for column, digest in remaining:
            initial[column].add(digest)
        return [len(values) for values in initial]

    generation = GenerationBudget(max_seconds=10.0, clock=lambda: 0.0)
    monkeypatch.setattr(generation, "remaining_seconds", lambda: 0.25)
    monkeypatch.setattr(single, "MAX_IN_MEMORY_DISTINCT", 4)
    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", count)
    single.profile_csv_bytes(_payload(), "records", budget=generation)
    assert seen == [0.25]
