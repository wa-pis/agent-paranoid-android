import json
from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.mcp_trino_server import mask_row
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.safety import (
    ProfileSafetyError,
    SourceRowReuseError,
    assert_no_csv_folder_source_rows,
    assert_no_csv_source_rows,
    assert_profile_safe,
)


def test_safe_profile_accepts_masked_sensitive_patterns() -> None:
    profile = DatasetProfile.model_validate(
        {
            "entities": [
                {
                    "name": "customers",
                    "row_count": 2,
                    "fields": [
                        {
                            "name": "email",
                            "data_type": "string",
                            "sensitive": True,
                            "semantic_type": "email",
                            "distribution": {
                                "kind": "masked_patterns",
                                "patterns": [{"pattern": "email", "count": 2}],
                            },
                        }
                    ],
                }
            ]
        }
    )

    assert_profile_safe(profile)


def test_safe_profile_rejects_raw_sensitive_categories_without_echoing_value() -> None:
    raw_email = "private-person@example.com"
    profile = DatasetProfile.model_validate(
        {
            "entities": [
                {
                    "name": "customers",
                    "row_count": 1,
                    "fields": [
                        {
                            "name": "email",
                            "data_type": "string",
                            "distribution": {
                                "kind": "categorical",
                                "categories": [{"value": raw_email, "count": 1}],
                            },
                        }
                    ],
                }
            ]
        }
    )

    with pytest.raises(ProfileSafetyError) as error:
        assert_profile_safe(profile)

    assert raw_email not in str(error.value)

    with pytest.raises(ProfileSafetyError):
        infer_dataset_spec(profile)


def test_spec_inference_marks_likely_sensitive_field_conservatively() -> None:
    profile = DatasetProfile.model_validate(
        {
            "entities": [
                {
                    "name": "customers",
                    "row_count": 1,
                    "fields": [{"name": "customer_email", "data_type": "string"}],
                }
            ]
        }
    )

    spec = infer_dataset_spec(profile)

    assert spec.entity("customers").field("customer_email").sensitive is True


def test_no_source_rows_check_rejects_exact_row_without_echoing_values(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    source.write_text("id,email\n1,alice@example.com\n")

    with pytest.raises(SourceRowReuseError) as error:
        assert_no_csv_source_rows(
            source,
            [{"id": "1", "email": "alice@example.com"}],
        )

    assert "alice@example.com" not in str(error.value)


def test_no_source_rows_check_accepts_fresh_synthetic_rows(tmp_path: Path) -> None:
    source = tmp_path / "customers.csv"
    source.write_text("id,email\n1,alice@example.com\n")

    assert_no_csv_source_rows(
        source,
        [{"id": 41000001, "email": "synthetic@example.test"}],
    )


def test_folder_source_row_check_uses_entity_file_names(tmp_path: Path) -> None:
    (tmp_path / "customers.csv").write_text("id,status\n1,active\n")

    with pytest.raises(SourceRowReuseError, match="customers"):
        assert_no_csv_folder_source_rows(
            tmp_path,
            {"customers": [{"id": "1", "status": "active"}]},
        )


def test_masked_row_matches_safe_snapshot() -> None:
    snapshot_path = Path(__file__).parent / "snapshots" / "masked_row.json"
    snapshot = json.loads(snapshot_path.read_text())
    masked = mask_row(
        {
            "customer_email": "alice@example.com",
            "api_token": "secret-token",
            "order_id": 123,
        }
    )

    assert masked == snapshot
    assert "alice@example.com" not in snapshot_path.read_text()
