"""Synthetic-only regressions for the public CSV inference pipeline."""

import csv
import json
from pathlib import Path

import pytest

from test_data_agent.adapters import csv_profile_to_dataset_spec
from test_data_agent.cli import main
from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.generation import generate_dataset
from test_data_agent.validation import validate_dataset


def source(tmp_path: Path, name: str, fields: list[str], rows: list[list[object]]) -> Path:
    path = tmp_path / f"{name}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)
    return path


@pytest.mark.parametrize("name", ["deal", "a_fairly_long_entity_name_for_forecasting_" * 2])
def test_pipeline_round_trip(tmp_path: Path, name: str) -> None:
    path = source(tmp_path, name, ["deal_id", "snapshot_id", "balance_ccy_val", "status"], [
        [f"record-{i:06d}", f"partition-{i % 2}", f"{-358377000000 + i}.25", "active" if i % 2 else "paused"]
        for i in range(2000)
    ])
    profile = profile_csv(path)
    spec = csv_profile_to_dataset_spec(profile, seed=7, count=50)
    rows = generate_dataset(spec, seed=7)
    assert validate_dataset(rows, spec).valid
    assert len({row["deal_id"] for row in rows[name]}) == 50
    assert len({row["snapshot_id"] for row in rows[name]}) == 2
    amount = next(column for column in profile.columns if column.name == "balance_ccy_val")
    assert amount.data_type == "float"
    assert not amount.sensitive
    assert rows == generate_dataset(spec, seed=7)


@pytest.mark.parametrize("distinct", [2000, 1400])
def test_distinct_after_value_tracking_limit(tmp_path: Path, distinct: int) -> None:
    path = source(tmp_path, "items", ["id"], [[i % distinct] for i in range(2000)])
    profile = profile_csv(path)
    assert profile.columns[0].approx_distinct_count == distinct
    normalized = legacy_profile_to_dataset_profile(profile.model_dump())
    assert normalized.entities[0].primary_key_candidates == (["id"] if distinct == 2000 else [])


def test_csv_local_categories_preserved_only_when_reviewed(tmp_path: Path) -> None:
    path = source(tmp_path, "items", ["status"], [["active"], ["paused"]] * 10)
    assert "active" not in profile_csv(path).model_dump_json()
    profile = profile_csv(path, local_category_fields=[LocalCategoryField(entity="items", field="status")])
    assert {item["value"] for item in profile.columns[0].top_values} == {"active", "paused"}
    spec = csv_profile_to_dataset_spec(profile, seed=7, count=50)
    assert {row["status"] for row in generate_dataset(spec, seed=7)["items"]} == {"active", "paused"}


def test_spaced_timezone_retains_timestamp(tmp_path: Path) -> None:
    path = source(tmp_path, "items", ["load_dttz"], [["2026-07-22 19:49:46.000 +0300"]])
    column = profile_csv(path).columns[0]
    assert column.data_type == "datetime"
    assert column.min_timestamp == "2026-07-22T19:49:46+03:00"


@pytest.mark.parametrize("field,value", [
    ("phone", "12025550101"), ("ssn", "123456789"),
    ("value", "sk_live_51ABCDEF"), ("cc", "4111111111111111"),
])
def test_sensitive_values_cannot_be_local_categories(tmp_path: Path, field: str, value: str) -> None:
    path = source(tmp_path, "items", [field], [[value]] * 20)
    assert profile_csv(path).columns[0].sensitive
    with pytest.raises(ValueError, match="sensitive"):
        profile_csv(path, local_category_fields=[LocalCategoryField(entity="items", field=field)])


def test_one_secret_among_amounts_is_still_sensitive(tmp_path: Path) -> None:
    path = source(tmp_path, "items", ["amount"], [["358377000000.25"]] * 200 + [["sk_live_51ABCDEF"]])
    profile = profile_csv(path)
    assert profile.columns[0].sensitive
    assert profile.columns[0].semantic_type == "secret"
    assert "sk_live_51ABCDEF" not in profile.model_dump_json()


def test_distinct_budget_cannot_claim_uniqueness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("test_data_agent.csv_profiler.MAX_DISTINCT_DIGESTS", 10)
    path = source(tmp_path, "items", ["id"], [[i] for i in range(10)])
    profile = profile_csv(path)
    assert profile.columns[0].approx_distinct_count < profile.row_count
    assert not legacy_profile_to_dataset_profile(profile.model_dump()).entities[0].primary_key_candidates


def test_sensitive_string_identifier_passes_final_privacy_validation() -> None:
    name = "long_entity_" * 6
    spec = DatasetSpec.model_validate({
        "entities": [{"name": name, "row_count": 10, "fields": [{
            "name": "record_id", "data_type": "string", "is_identifier": True,
            "sensitive": True, "semantic_type": "secret",
            "distribution": {"kind": "synthetic_identifier"},
        }]}],
    })
    rows = generate_dataset(spec, seed=7)
    assert validate_dataset(rows, spec).valid


def test_cli_profile_infer_generate_round_trip(tmp_path: Path) -> None:
    name = "a_long_financial_entity_for_pipeline_regression"
    path = source(tmp_path, name, ["id", "snapshot_id", "amount_ccy_val", "status"], [
        [f"record-{i}", f"partition-{i % 2}", f"{-358377000000 + i}.25", "active"]
        for i in range(2000)
    ])
    profile = tmp_path / "profile.json"
    spec = tmp_path / "spec.yaml"
    output = tmp_path / "generated"
    assert main(["profile-csv", str(path), "--local-category", f"{name}.status", "--output", str(profile)]) == 0
    assert main(["infer-spec", str(profile), "--count", "50", "--output", str(spec)]) == 0
    assert main(["generate", str(spec), "--seed", "7", "--format", "json", "--output", str(output)]) == 0
    rows = json.loads((output / f"{name}.json").read_text())
    assert len(rows) == 50
    assert len({row["id"] for row in rows}) == 50
    assert len({row["snapshot_id"] for row in rows}) == 2
    assert {row["status"] for row in rows} == {"active"}
