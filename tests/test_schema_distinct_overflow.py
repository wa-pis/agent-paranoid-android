import pytest

from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.profiling.schema_profiler import MAX_DISTINCT_TRACKED, FieldAccumulator, profile_schema


def test_untracked_duplicates_do_not_claim_full_uniqueness(tmp_path):
    values = list(range(MAX_DISTINCT_TRACKED + 1)) + [MAX_DISTINCT_TRACKED] * 1000
    (tmp_path / "items.csv").write_text(
        "id\n" + "\n".join(map(str, values)) + "\n", encoding="utf-8",
    )
    entity = profile_schema(tmp_path).entities[0]
    assert entity.fields[0].unique_ratio < 0.98
    assert entity.fields[0].unique_ratio_kind == "lower_bound"
    assert "id" not in entity.primary_key_candidates


@pytest.mark.parametrize("count", [0, 10, MAX_DISTINCT_TRACKED, MAX_DISTINCT_TRACKED + 1])
def test_cap_boundary_and_roundtrip(count):
    accumulator = FieldAccumulator(name="id")
    for value in range(count):
        accumulator.add(str(value))
    accumulator.add(None)
    profile = accumulator.to_profile(count + 1)
    overflow = count > MAX_DISTINCT_TRACKED
    assert profile.unique_ratio_kind == ("lower_bound" if overflow else "exact")
    assert profile.unique_ratio <= (min(count, MAX_DISTINCT_TRACKED) / count if count else 0)
    assert len(accumulator.distinct_values) <= MAX_DISTINCT_TRACKED
    assert FieldProfile.model_validate_json(profile.model_dump_json()) == profile


def test_overflow_excludes_key_even_with_high_lower_bound(tmp_path):
    (tmp_path / "items.csv").write_text(
        "id\n" + "\n".join(map(str, range(MAX_DISTINCT_TRACKED + 1))) + "\n",
        encoding="utf-8",
    )
    entity = profile_schema(tmp_path).entities[0]
    assert entity.fields[0].unique_ratio >= 0.98
    assert not entity.primary_key_candidates


def test_legacy_profile_does_not_claim_exact_measurement():
    profile = FieldProfile(name="id", data_type=FieldType.INTEGER, unique_ratio=1.0)
    assert profile.unique_ratio_kind == "unspecified"
