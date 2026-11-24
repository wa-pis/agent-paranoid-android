import hashlib
import json

import pytest

from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.io.artifacts import dataset_profile_fingerprint
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.cache import PROFILE_CACHE_FORMAT_VERSION, cache_path, csv_folder_fingerprint
from test_data_agent.profiling.schema_profiler import FieldAccumulator, profile_schema


@pytest.mark.parametrize("duplicate_count", [1, 1000])
def test_duplicates_beyond_former_cap_are_counted(tmp_path, duplicate_count):
    values = list(range(10_001)) + [10_000] * duplicate_count
    (tmp_path / "items.csv").write_text(
        "id\n" + "\n".join(map(str, values)) + "\n", encoding="utf-8",
    )
    entity = profile_schema(tmp_path).entities[0]
    assert entity.fields[0].unique_ratio == round(10_001 / (10_001 + duplicate_count), 6)
    assert entity.fields[0].unique_ratio_kind == "exact"
    assert entity.fields[0].distribution["pool_size"] == 10_001
    assert "id" not in entity.primary_key_candidates


@pytest.mark.parametrize("count", [0, 10, 10_000, 10_001, 20_001])
def test_distinct_tracking_and_roundtrip(count):
    accumulator = FieldAccumulator(name="id")
    for value in range(count):
        accumulator.add(str(value))
    accumulator.add(None)
    profile = accumulator.to_profile(count + 1)
    assert profile.unique_ratio_kind == "exact"
    assert profile.unique_ratio == (1 if count else 0)
    assert len(accumulator.distinct_digests) == count
    assert all(type(digest) is bytes and len(digest) == 32 for digest in accumulator.distinct_digests)
    assert FieldProfile.model_validate_json(profile.model_dump_json()) == profile


def test_large_unique_column_nominates_key_and_generates_unique_rows(tmp_path):
    (tmp_path / "items.csv").write_text(
        "id\n" + "\n".join(map(str, range(10_001))) + "\n",
        encoding="utf-8",
    )
    profile = profile_schema(tmp_path)
    entity = profile.entities[0]
    assert entity.fields[0].unique_ratio == 1
    assert entity.primary_key_candidates == ["id"]
    spec = infer_dataset_spec(profile)
    rows = generate_dataset(spec, seed=1)["items"]
    ids = {row["id"] for row in rows}
    assert len(rows) == len(ids) == 10_001
    assert ids.isdisjoint(range(10_001))


def test_legacy_profile_does_not_claim_exact_measurement():
    profile = FieldProfile(name="id", data_type=FieldType.INTEGER, unique_ratio=1.0)
    assert profile.unique_ratio_kind == "unspecified"


def test_persisted_profile_keeps_legacy_fingerprint(tmp_path):
    profile = DatasetProfile(entities=[EntityProfile(name="items", row_count=1, fields=[
        FieldProfile(name="id", data_type=FieldType.INTEGER, unique_ratio=1.0),
    ])])
    legacy = profile.model_dump(mode="json")
    legacy.pop("local_category_fields")
    legacy.pop("has_unmodeled_expressions", None)
    legacy["entities"][0]["fields"][0].pop("unique_ratio_kind")
    expected = hashlib.sha256(json.dumps(legacy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")
    loaded = DatasetProfile.model_validate_json(path.read_text(encoding="utf-8"))
    assert dataset_profile_fingerprint(loaded) == expected
    loaded.entities[0].fields[0].unique_ratio_kind = "lower_bound"
    assert dataset_profile_fingerprint(loaded) != expected


@pytest.mark.parametrize("old_version", [2, 4, 9])
def test_old_cache_is_reprofiled_with_full_distinct_evidence(tmp_path, old_version):
    source = tmp_path / "source"
    source.mkdir()
    (source / "items.csv").write_text(
        "id\n" + "\n".join(map(str, range(10_001))) + "\n",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    fingerprint = csv_folder_fingerprint(source)
    old_profile = DatasetProfile(entities=[EntityProfile(
        name="items", row_count=10_001,
        fields=[FieldProfile(name="id", data_type=FieldType.INTEGER,
                            unique_ratio=0.9999, unique_ratio_kind="lower_bound", is_identifier=True)],
    )]).model_dump(mode="json")
    if old_version == 2:
        old_profile["entities"][0]["fields"][0].pop("unique_ratio_kind")
    cache_path(cache, fingerprint).write_text(json.dumps({
        "format_version": old_version, "fingerprint": fingerprint, "profile": old_profile,
    }), encoding="utf-8")
    fresh = profile_example_folder(source, cache_dir=cache)
    assert fresh.entities[0].fields[0].unique_ratio_kind == "exact"
    assert fresh.entities[0].fields[0].unique_ratio == 1
    assert fresh.entities[0].primary_key_candidates == ["id"]
    cached_text = cache_path(cache, fingerprint).read_text()
    assert json.loads(cached_text)["format_version"] == PROFILE_CACHE_FORMAT_VERSION
    assert "distinct_digests" not in cached_text
    assert profile_example_folder(source, cache_dir=cache) == fresh
