"""Profile safety cannot depend on a caller-selected source label."""

from __future__ import annotations

import pytest

from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget, InputLimitError
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.generation.planner import InferenceMetadataError
from test_data_agent.safety import assert_profile_safe, assert_spec_safe


SOURCE_TYPES = (
    "csv", "csv_folder", "parquet", "postgres", "postgres_query", "trino",
    "trino_query", "json_profile", "legacy_profile", "custom",
)
EXACT_SUMMARIES = {
    "min_value": 12731.25, "max_value": 92737.75,
    "p05": 12871.5, "p95": 81291.5,
}


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
@pytest.mark.parametrize("classification", ["flag", "name", "semantic"])
def test_legacy_sensitive_summaries_are_suppressed_for_every_source(
    source_type: str, classification: str,
) -> None:
    name = "customer_email" if classification == "name" else "payload"
    profile = legacy_profile_to_dataset_profile({
        "table": "records", "row_count": 2,
        "columns": [{
            "name": name, "data_type": "double", "approx_distinct_count": 2,
            "sensitive": classification == "flag",
            "semantic_type": "ssn" if classification == "semantic" else None,
            **EXACT_SUMMARIES,
        }],
    }, source_type=source_type)

    field = profile.entity("records").field(name)
    assert field.sensitive
    assert field.distribution == {}
    assert_profile_safe(profile)
    if source_type in {"postgres_query", "trino_query"}:
        with pytest.raises(InferenceMetadataError, match="requires reprofiling"):
            infer_dataset_spec(profile)
        profile = profile.model_copy(update={"has_unmodeled_expressions": False})
    spec = infer_dataset_spec(profile)
    for serialized in (profile.model_dump_json(), spec.model_dump_json()):
        assert all(str(value) not in serialized for value in EXACT_SUMMARIES.values())


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
@pytest.mark.parametrize("kind", ["numeric_shape", "masked_patterns", "synthetic_identifier"])
def test_safe_sensitive_distributions_survive_normalization_for_every_source(
    source_type: str, kind: str,
) -> None:
    name = "account_id" if kind == "synthetic_identifier" else "payload"
    profile = legacy_profile_to_dataset_profile({
        "table": "records", "row_count": 2,
        "columns": [{
            "name": name, "data_type": "bigint", "sensitive": True,
            "approx_distinct_count": 2,
            "numeric_shape": {
                "kind": "numeric", "max_abs_magnitude": 3,
                "has_negative": False, "has_positive": True, **EXACT_SUMMARIES,
            } if kind == "numeric_shape" else None,
            "masked_patterns": [{"pattern": "text_len_6", "count": 2}]
            if kind == "masked_patterns" else [],
            **EXACT_SUMMARIES,
        }],
    }, source_type=source_type)

    field = profile.entity("records").field(name)
    assert field.sensitive
    assert field.distribution["kind"] == kind
    assert_profile_safe(profile)
    assert all(str(value) not in profile.model_dump_json() for value in EXACT_SUMMARIES.values())


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
def test_non_sensitive_summaries_remain_available_for_every_source(source_type: str) -> None:
    summaries = {"min_value": 12.5, "max_value": 92.75, "p05": 12.8, "p95": 81.25}
    profile = legacy_profile_to_dataset_profile({
        "table": "records", "row_count": 2,
        "columns": [{"name": "quantity", "data_type": "double", **summaries}],
    }, source_type=source_type)

    field = profile.entity("records").field("quantity")
    assert not field.sensitive
    assert field.distribution["kind"] == "numeric"
    assert all(field.distribution[key] == value for key, value in summaries.items())
    assert_profile_safe(profile)


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
@pytest.mark.parametrize("distinct_count", [4, 100])
def test_lower_bound_cardinality_cannot_create_a_pool_or_primary_key(
    source_type: str, distinct_count: int,
) -> None:
    profile = legacy_profile_to_dataset_profile({
        "table": "records", "row_count": 100,
        "columns": [{
            "name": "record_id", "data_type": "bigint",
            "approx_distinct_count": distinct_count, "unique_ratio_kind": "lower_bound",
        }],
    }, source_type=source_type)

    entity = profile.entity("records")
    field = entity.field("record_id")
    assert field.unique_ratio_kind == "lower_bound"
    assert "pool_size" not in field.distribution
    assert entity.primary_key_candidates == []


@pytest.mark.parametrize("kind,expected_pool", [
    ("exact", 99_999), ("unspecified", None), ("lower_bound", None),
])
def test_csv_exact_cardinality_bypasses_only_the_historical_censor(
    kind: str, expected_pool: int | None,
) -> None:
    profile = legacy_profile_to_dataset_profile({
        "table": "records", "row_count": 100_001,
        "columns": [{
            "name": "record_id", "data_type": "bigint",
            "approx_distinct_count": 99_999, "unique_ratio_kind": kind,
        }],
    }, source_type="csv")

    field = profile.entity("records").field("record_id")
    assert field.unique_ratio_kind == kind
    assert field.distribution.get("pool_size") == expected_pool


def test_generated_rank_metadata_does_not_consume_the_raw_cell_limit(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        b"kind\nx\n", "items", budget=GenerationBudget(5),
    ))
    field = profile.entity("items").field("kind")
    assert field.distribution["categories"] == [{"value": "category_1", "count": 1}]
    assert_profile_safe(profile)
    assert_spec_safe(infer_dataset_spec(profile))


@pytest.mark.parametrize("candidate", ["category_1", "category_20_20", "category_50"])
def test_generated_rank_scope_still_runs_the_full_detector(candidate, monkeypatch) -> None:
    import test_data_agent.core.privacy as privacy

    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    original = privacy.infer_source_value_signal
    calls = []

    def capture(value, *, max_chars=None):
        calls.append((value, max_chars))
        return original(value, max_chars=max_chars)

    monkeypatch.setattr(privacy, "infer_source_value_signal", capture)
    assert privacy.infer_category_value_signal(candidate) is None
    assert calls == [(candidate, len(candidate))]
    with pytest.raises(InputLimitError, match="character limit"):
        original(candidate)


def test_category_rank_lookalike_cannot_bypass_limits_or_privacy(monkeypatch) -> None:
    from test_data_agent.core.privacy import infer_category_value_signal

    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    candidate = "category_1 password=synthetic_value"
    with pytest.raises(InputLimitError, match="character limit"):
        infer_category_value_signal(candidate)
    assert infer_category_value_signal(candidate, max_chars=64).strong_secret
    profile = legacy_profile_to_dataset_profile({
        "table": "items", "row_count": 1,
        "columns": [{"name": "kind", "data_type": "string",
                     "top_values": [{"value": candidate, "count": 1}]}],
    }, max_chars=64)
    assert profile.entity("items").field("kind").sensitive
    assert candidate not in profile.model_dump_json()
