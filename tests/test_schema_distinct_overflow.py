import hashlib
import json

import pytest

from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.io.artifacts import dataset_profile_fingerprint
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.cache import cache_path, csv_folder_fingerprint
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


def test_persisted_profile_keeps_legacy_fingerprint(tmp_path):
    profile = DatasetProfile(entities=[EntityProfile(name="items", row_count=1, fields=[
        FieldProfile(name="id", data_type=FieldType.INTEGER, unique_ratio=1.0),
    ])])
    legacy = profile.model_dump(mode="json")
    legacy.pop("local_category_fields")
    legacy["entities"][0]["fields"][0].pop("unique_ratio_kind")
    expected = hashlib.sha256(json.dumps(legacy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")
    loaded = DatasetProfile.model_validate_json(path.read_text(encoding="utf-8"))
    assert dataset_profile_fingerprint(loaded) == expected
    loaded.entities[0].fields[0].unique_ratio_kind = "lower_bound"
    assert dataset_profile_fingerprint(loaded) != expected


def test_old_cache_is_reprofiled_with_uncertainty(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "items.csv").write_text(
        "id\n" + "\n".join(map(str, range(MAX_DISTINCT_TRACKED + 1))) + "\n",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    fingerprint = csv_folder_fingerprint(source)
    old_profile = DatasetProfile(entities=[EntityProfile(
        name="items", row_count=MAX_DISTINCT_TRACKED + 1, primary_key_candidates=["id"],
        fields=[FieldProfile(name="id", data_type=FieldType.INTEGER, unique_ratio=1.0, is_identifier=True)],
    )]).model_dump(mode="json")
    old_profile["entities"][0]["fields"][0].pop("unique_ratio_kind")
    cache_path(cache, fingerprint).write_text(json.dumps({
        "format_version": 2, "fingerprint": fingerprint, "profile": old_profile,
    }), encoding="utf-8")
    fresh = profile_example_folder(source, cache_dir=cache)
    assert fresh.entities[0].fields[0].unique_ratio_kind == "lower_bound"
    assert not fresh.entities[0].primary_key_candidates
    assert profile_example_folder(source, cache_dir=cache) == fresh
