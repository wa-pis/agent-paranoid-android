import pytest

from test_data_agent.adapters.csv_file import csv_file_to_dataset_profile
from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.distribution import SyntheticIdentifierDistribution
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.csv_profiler import MAX_DISTINCT_DIGESTS
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.profiling.schema_profiler import profile_schema


@pytest.mark.parametrize("count", [2, 100, 1000])
@pytest.mark.parametrize("route", ["csv", "folder", "aggregate"])
def test_fixed_key_pool_across_output_sizes(tmp_path, count, route):
    source = tmp_path / "events.csv"
    source.write_text("run_id\n" + "\n".join(["11", "22", "33", "44"] * 25) + "\n")
    if route == "csv":
        profile = csv_file_to_dataset_profile(source)
    elif route == "folder":
        profile = profile_schema(tmp_path)
    else:
        profile = legacy_profile_to_dataset_profile({
            "table": "events", "row_count": 100,
            "columns": [{"name": "run_id", "data_type": "integer", "approx_distinct_count": 4}],
        })
    spec = infer_dataset_spec(profile, count=count)
    assert spec.entities[0].primary_key is None
    assert spec.entities[0].fields[0].distribution["pool_size"] == 4
    spec = DatasetSpec.model_validate_json(spec.model_dump_json())
    rows = generate_dataset(spec, seed=7)
    keys = {row["run_id"] for row in rows["events"]}
    assert len(keys) == min(count, 4)
    assert keys.isdisjoint({11, 22, 33, 44})
    assert rows == generate_dataset(spec, seed=7)


@pytest.mark.parametrize("size", [0, -1, True, 1.5, "4"])
def test_pool_size_requires_positive_integer(size):
    with pytest.raises(ValueError):
        SyntheticIdentifierDistribution(pool_size=size)


def test_absent_pool_preserves_old_distribution_serialization():
    assert SyntheticIdentifierDistribution().model_dump() == {"kind": "synthetic_identifier", "prefix": None}


def test_small_pool_cannot_claim_primary_key():
    with pytest.raises(ValueError, match="primary key pool"):
        DatasetSpec.model_validate({"entities": [{"name": "events", "row_count": 10,
            "primary_key": "id", "fields": [{"name": "id", "data_type": "integer",
            "is_identifier": True, "distribution": {"kind": "synthetic_identifier", "pool_size": 4}}]}]})


@pytest.mark.parametrize("data_type", ["integer", "string"])
def test_pools_keep_independent_domains_and_null_behavior(data_type):
    spec = DatasetSpec(entities=[EntitySpec(name="events", row_count=100, fields=[
        FieldSpec(name=name, data_type=data_type, is_identifier=True,
                  nullable=True, null_ratio=0.25,
                  distribution={"kind": "synthetic_identifier", "pool_size": 4})
        for name in ("left_id", "right_id")
    ])])
    rows = generate_dataset(spec, seed=7)["events"]
    domains = [{row[name] for row in rows if row[name] is not None}
               for name in ("left_id", "right_id")]
    assert all(len(domain) == 4 for domain in domains)
    assert domains[0].isdisjoint(domains[1])
    assert any(row["left_id"] is None for row in rows)


def test_nearly_unique_folder_key_is_not_a_primary_key(tmp_path):
    (tmp_path / "events.csv").write_text(
        "run_id\n" + "\n".join(str(i) for i in [*range(99), 0]) + "\n"
    )
    profile = profile_schema(tmp_path)
    assert profile.entities[0].primary_key_candidates == []
    assert profile.entities[0].fields[0].distribution["pool_size"] == 99


def test_censored_csv_count_does_not_create_a_pool():
    profile = legacy_profile_to_dataset_profile({
        "table": "events", "row_count": MAX_DISTINCT_DIGESTS * 2,
        "columns": [{"name": "run_id", "data_type": "integer",
                     "approx_distinct_count": MAX_DISTINCT_DIGESTS - 1}],
    }, source_type="csv")
    assert "pool_size" not in profile.entities[0].fields[0].distribution
