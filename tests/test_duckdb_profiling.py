"""Complete synthetic CSV-profile equivalence across distinct implementations."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("pyarrow")

from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.io.artifacts import dataset_profile_fingerprint, dataset_spec_fingerprint
from test_data_agent.profiling import profile_example_folder, profile_schema
from test_data_agent.profiling import schema_profiler


FIXTURE = Path(__file__).parent / "fixtures" / "example_dataset"


def assert_identical_profiles(left: Any, right: Any) -> None:
    assert left.model_dump(mode="json") == right.model_dump(mode="json")
    assert dataset_profile_fingerprint(left) == dataset_profile_fingerprint(right)
    left_spec, right_spec = infer_dataset_spec(left), infer_dataset_spec(right)
    assert left_spec.model_dump(mode="json") == right_spec.model_dump(mode="json")
    assert dataset_spec_fingerprint(left_spec) == dataset_spec_fingerprint(right_spec)


@pytest.mark.parametrize("entrypoint", [profile_schema, profile_example_folder])
def test_complete_linked_profile_matches_set(
    monkeypatch: pytest.MonkeyPatch, entrypoint: Any,
) -> None:
    kwargs = {"cache_dir": None} if entrypoint is profile_example_folder else {}
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10**9)
    expected = entrypoint(FIXTURE, **kwargs)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 0)

    actual = entrypoint(FIXTURE, **kwargs)

    assert_identical_profiles(expected, actual)
    if entrypoint is profile_example_folder:
        assert actual.relationships
        assert {constraint.type for constraint in actual.constraints} >= {
            ConstraintType.FORMULA, ConstraintType.TEMPORAL,
            ConstraintType.CONDITIONAL_REQUIRED, ConstraintType.AGGREGATE_MAPPING,
        }


def write_edge_corpus(source: Path) -> None:
    (source / "a_empty.csv").write_text("id,all_null\n", encoding="utf-8")
    fields = [
        "record_id", "leading_label", "trimmed", "flag", "event_date", "moment",
        "huge", "amount", "status", "detail", "all_null", "late_evidence",
        "overflow_labels",
    ]
    with (source / "b_events.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(fields)
        for index in range(2_103):
            active = index % 3 != 2
            writer.writerow([
                f"R{index:05}" if index != 2_102 else "R00000",
                ("0001", "1", "00001")[index % 3],
                ("\u2003alpha\u00a0", "alpha", " \tbeta\t ", "", "\n")[index % 5],
                "TRUE" if index % 2 else "false",
                f"2024-03-{index % 28 + 1:02}",
                "2026-07-22 19:49:46.000 +0300",
                9_007_199_254_740_993 + index,
                f"-{index % 40 + 1}.25",
                "active" if active else "paused",
                "filled" if active else "",
                "" if index % 2 else " \u2003",
                "-1.25" if index < 2_102 else "sk_live_51ABCDEF",
                f"label-{index % 1_001}",
            ])
    (source / "c_labels.csv").write_bytes(
        "label_id;label\nA01;café\nA02;niño\nA03; café \n".encode("latin-1")
    )


def test_full_profile_sampling_normalization_and_late_evidence_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_edge_corpus(tmp_path)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10**9)
    expected = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=37)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 0)

    actual = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=37)

    assert_identical_profiles(expected, actual)
    events = actual.entity("b_events")
    assert events.row_count == 2_103
    assert events.field("record_id").distribution["pool_size"] == 2_102
    assert events.field("record_id").unique_ratio == round(2_102 / 2_103, 6)
    assert "record_id" not in events.primary_key_candidates
    assert events.field("leading_label").unique_ratio == round(3 / 2_103, 6)
    assert events.field("all_null").null_ratio == 1
    assert events.field("late_evidence").sensitive
    assert events.field("late_evidence").semantic_type == "secret"
    assert "sk_live_51ABCDEF" not in actual.model_dump_json()
    assert actual.entity("a_empty").row_count == 0


def test_automatic_crossover_preserves_earlier_values_and_late_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from test_data_agent.profiling import duckdb_distinct

    (tmp_path / "items.csv").write_text(
        "item_id,group_id,optional\n"
        + "".join(f"I{index},G{index % 3},{'value' if index % 2 else ''}\n"
                  for index in range(30))
        + "I0,G0,value\nI29,G2,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10**9)
    expected = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=7)
    calls = 0
    original_count = duckdb_distinct.count_distinct_stream

    def count_stream(*args: Any, **kwargs: Any) -> list[int]:
        nonlocal calls
        calls += 1
        return original_count(*args, **kwargs)

    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", count_stream)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10)

    actual = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=7)

    assert calls == 1
    assert_identical_profiles(expected, actual)
    assert actual.entity("items").field("item_id").distribution["pool_size"] == 30


def test_local_categories_and_cache_are_independent_of_distinct_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from test_data_agent.profiling import duckdb_distinct

    source = tmp_path / "source"
    source.mkdir()
    (source / "events.csv").write_text(
        "event_id,status,detail\n1,active,filled\n2,active,filled\n3,paused,\n",
        encoding="utf-8",
    )
    allowed = (LocalCategoryField(entity="events", field="status"),)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10**9)
    expected = profile_example_folder(source, cache_dir=None, local_category_fields=allowed)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 0)
    cache = tmp_path / "cache"
    actual = profile_example_folder(source, cache_dir=cache, local_category_fields=allowed)

    assert_identical_profiles(expected, actual)
    assert {item["value"] for item in actual.entity("events").field("status").distribution["categories"]} == {
        "active", "paused",
    }

    def forbidden_stream(*args: Any, **kwargs: Any) -> list[int]:
        raise AssertionError("a cache hit must not initialize DuckDB")

    monkeypatch.setattr(duckdb_distinct, "count_distinct_stream", forbidden_stream)
    cached = profile_example_folder(source, cache_dir=cache, local_category_fields=allowed)

    assert_identical_profiles(actual, cached)
    assert len(list(cache.glob("*.json"))) == 1


def test_switching_does_not_reopen_csv_text_or_change_rule_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "events.csv"
    source.write_text(
        "event_id,status,detail\n"
        + "".join(f"I{index},active,filled\n" for index in range(20))
        + "I0,paused,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 10**9)
    expected = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=7)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 5)
    original_open = Path.open
    text_opens = 0

    def counting_open(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        nonlocal text_opens
        if path == source and "b" not in mode:
            text_opens += 1
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counting_open)

    actual = profile_example_folder(tmp_path, cache_dir=None, rule_sample_rows=7)

    assert text_opens == 1
    assert_identical_profiles(expected, actual)
