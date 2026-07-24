import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from test_data_agent.adapters import (
    dataset_profile_from_csv_file,
    dataset_profile_from_csv_folder,
    dataset_profile_from_parquet,
    dataset_spec_from_csv_folder,
    dataset_spec_from_trino_profile,
    load_profile_or_spec,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import InputLimitError


FIXTURE_CSV = Path(__file__).parent / "fixtures" / "customers.csv"
FIXTURE_FOLDER = Path(__file__).parent / "fixtures" / "example_dataset"


def test_csv_file_adapter_builds_safe_one_entity_profile() -> None:
    profile = dataset_profile_from_csv_file(FIXTURE_CSV)
    profile_json = profile.model_dump_json()
    customers = profile.entity("customers")
    email = customers.field("email")

    assert profile.source_type == "csv"
    assert customers.row_count == 5
    assert email.sensitive is True
    assert email.distribution["kind"] == "masked_patterns"
    assert "alice@example.com" not in profile_json


def test_json_adapter_does_not_treat_broken_dataset_profile_as_legacy(tmp_path) -> None:
    profile_path = tmp_path / "broken_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "source_type": "csv_folder",
                "entities": [],
                "relationships": [
                    {
                        "parent_entity": "customers",
                        "parent_field": "customer_id",
                        "child_entity": "orders",
                        "child_field": "customer_id",
                        "confidence": 1.0,
                    }
                ],
            }
        )
    )

    with pytest.raises(ValidationError, match="relationship references unknown entity"):
        load_profile_or_spec(profile_path)


def test_csv_folder_adapter_builds_safe_multi_entity_profile() -> None:
    profile = dataset_profile_from_csv_folder(FIXTURE_FOLDER, use_cache=False)
    customers = profile.entity("customers")

    assert profile.source_type == "csv_folder"
    assert {entity.name for entity in profile.entities} == {"customers", "orders"}
    assert customers.field("email").sensitive is True
    assert any(
        relationship.parent_entity == "customers"
        and relationship.child_entity == "orders"
        for relationship in profile.relationships
    )
    assert "alice@example.com" not in profile.model_dump_json()


def test_csv_folder_profile_masks_secret_in_neutrally_named_column(tmp_path: Path) -> None:
    source = tmp_path / "settings.csv"
    source.write_text("value\nsk_live_51ABCDEF\nsk_live_51ABCDEF\n")

    profile = dataset_profile_from_csv_folder(tmp_path, use_cache=False)
    value = profile.entity("settings").field("value")

    assert value.sensitive is True
    assert value.distribution["kind"] == "masked_patterns"
    assert "sk_live_51ABCDEF" not in profile.model_dump_json()


def test_csv_folder_adapter_builds_dataset_spec_with_seed_and_relationships() -> None:
    spec = dataset_spec_from_csv_folder(FIXTURE_FOLDER, count=7, seed=123, use_cache=False)

    assert spec.generation_settings.seed == 123
    assert spec.entity("customers").row_count == 7
    assert spec.entity("orders").row_count == 7
    assert any(
        relationship.parent_entity == "customers"
        and relationship.child_entity == "orders"
        for relationship in spec.relationships
    )


def test_trino_profile_adapter_uses_safe_metadata_only() -> None:
    spec = dataset_spec_from_trino_profile(
        {
            "source_type": "trino",
            "table": "orders",
            "row_count": 100,
            "columns": [
                {"name": "order_id", "data_type": "bigint", "approx_distinct_count": 100, "non_null_count": 100},
                {
                    "name": "status",
                    "data_type": "varchar",
                    "top_values": [{"value": "paid", "count": 80}, {"value": "cancelled", "count": 20}],
                    "approx_distinct_count": 2,
                    "non_null_count": 100,
                },
                {
                    "name": "customer_email",
                    "data_type": "varchar",
                    "top_values": [{"value": "alice@example.com", "count": 1}],
                    "approx_distinct_count": 100,
                    "non_null_count": 100,
                },
            ],
        },
        count=10,
    )

    orders = spec.entity("orders")
    email = orders.field("customer_email")
    status = orders.field("status")

    assert orders.row_count == 10
    assert orders.primary_key == "order_id"
    assert status.distribution["kind"] == "categorical"
    assert email.sensitive is True
    assert "alice@example.com" not in spec.model_dump_json()


def test_older_profile_payload_masks_secret_in_neutral_top_values() -> None:
    spec = dataset_spec_from_trino_profile(
        {
            "source_type": "trino",
            "table": "settings",
            "row_count": 2,
            "columns": [
                {
                    "name": "value",
                    "data_type": "varchar",
                    "top_values": [{"value": "sk_live_51ABCDEF", "count": 2}],
                    "approx_distinct_count": 1,
                    "non_null_count": 2,
                }
            ],
        },
        count=2,
    )

    value = spec.entity("settings").field("value")

    assert value.sensitive is True
    assert value.distribution["kind"] == "masked_patterns"
    assert "sk_live_51ABCDEF" not in spec.model_dump_json()


def test_json_loader_distinguishes_profiles_from_specs(tmp_path) -> None:
    profile_path = tmp_path / "profile.json"
    spec_path = tmp_path / "spec.json"

    profile_path.write_text(
        json.dumps(
            {
                "source_type": "csv",
                "entities": [{"name": "customers", "row_count": 1, "fields": [], "primary_key_candidates": []}],
            }
        )
    )
    spec_path.write_text(json.dumps({"entities": [{"name": "customers", "row_count": 1, "fields": []}]}))

    assert isinstance(load_profile_or_spec(profile_path), DatasetProfile)
    assert isinstance(load_profile_or_spec(spec_path), DatasetSpec)


def test_parquet_adapter_uses_schema_metadata(tmp_path) -> None:
    path = tmp_path / "customers.parquet"
    table = pa.table({"customer_id": [1, 2], "active": [True, False], "score": [1.5, 2.5]})
    pq.write_table(table, path)

    profile = dataset_profile_from_parquet(path)
    customers = profile.entity("customers")

    assert profile.source_type == "parquet"
    assert customers.row_count == 2
    assert customers.field("customer_id").is_identifier is True
    assert customers.field("active").data_type == "boolean"
    assert customers.field("score").data_type == "float"


def test_parquet_adapter_rejects_row_count_before_reading_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "customers.parquet"
    pq.write_table(pa.table({"id": [1, 2]}), path)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_ROWS", "1")

    with pytest.raises(InputLimitError, match="<= 1 rows"):
        dataset_profile_from_parquet(path)
