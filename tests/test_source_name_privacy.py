"""Name-based risk is conservative and independent of the source adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from test_data_agent.adapters.json_profile import json_payload_to_dataset_profile
from test_data_agent.adapters.parquet_dataset import dataset_profile_from_parquet
from test_data_agent.core.privacy import infer_sensitive_from_name
from test_data_agent.core.semantics import semantic_name_hint
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.generation.planner import InferenceMetadataError


_ALIASES = (
    "apiKey", "APIKey", "api_key", "api key", "api-key", "clientAPIKey",
    "accessKey", "access_key", "access.key", "vaultPrivateKey", "private-key",
    "taxId", "billingTaxID", "PAN", "paymentPAN", "pan_code", "CC", "paymentCC",
    "ccCode", "passwd", "clientPasswd", "apiKeyCount", "panCount", "apiKeyPAN",
)
_SOURCE_LABELS = (
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile",
    "postgres", "postgres_query", "trino", "trino_query",
)


@pytest.mark.parametrize("name", _ALIASES)
def test_sensitive_name_aliases_require_protection(name: str) -> None:
    assert infer_sensitive_from_name(name)


@pytest.mark.parametrize("name", [
    "key", "primaryKey", "hash", "identifier", "monkey", "panorama",
    "occupancy", "ccount", "apiaryKey", "accessoryKey", "privateerKey", "taxIdentifier",
])
def test_sensitive_name_aliases_do_not_match_embedded_or_generic_words(name: str) -> None:
    assert not infer_sensitive_from_name(name)


def test_all_legacy_sensitive_name_fragments_remain_sensitive() -> None:
    fragments = (
        "address", "birth", "card", "credential", "dob", "email", "first_name",
        "firstname", "full_name", "last_name", "lastname", "mail", "name", "passport",
        "password", "phone", "secret", "ssn", "tax_id", "token", "user", "username",
    )
    for fragment in fragments:
        assert infer_sensitive_from_name(f"prefix{fragment}suffix")
    assert infer_sensitive_from_name("prefix_cc_suffix")
    assert infer_sensitive_from_name("cardinality")


def test_conflicting_or_numeric_semantic_hints_do_not_remove_name_based_risk() -> None:
    assert semantic_name_hint("apiKeyPAN", numeric=False) is None
    assert semantic_name_hint("apiKeyCount", numeric=True) is None
    assert semantic_name_hint("panCount", numeric=True) is None
    assert all(infer_sensitive_from_name(name) for name in (
        "apiKeyPAN", "apiKeyCount", "panCount",
    ))


@pytest.mark.parametrize("source_type", _SOURCE_LABELS)
def test_legacy_json_name_protection_is_independent_of_source_label(source_type: str) -> None:
    profile = json_payload_to_dataset_profile({
        "source_type": source_type,
        "table": "records",
        "row_count": 0,
        "columns": [
            {"name": name, "data_type": "integer", "sensitive": False}
            for name in _ALIASES
        ],
    })
    assert profile.source_type == source_type
    for field in profile.entity("records").fields:
        assert field.sensitive
        assert field.data_type == "integer"
        assert field.semantic_type is None
        assert field.distribution == {}


@pytest.mark.parametrize("source_type", _SOURCE_LABELS)
def test_typed_json_profiles_cannot_declassify_names_during_spec_inference(source_type: str) -> None:
    profile = json_payload_to_dataset_profile({
        "source_type": source_type,
        "entities": [{
            "name": "records", "row_count": 0,
            "fields": [{"name": "apiKeyCount", "data_type": "integer", "sensitive": False}],
        }],
    })
    assert not profile.entity("records").field("apiKeyCount").sensitive

    if source_type in {"postgres_query", "trino_query"}:
        with pytest.raises(InferenceMetadataError, match="requires reprofiling"):
            infer_dataset_spec(profile, count=2)
        profile = profile.model_copy(update={"has_unmodeled_expressions": False})
    field = infer_dataset_spec(profile, count=2).entity("records").field("apiKeyCount")
    assert field.sensitive
    assert field.data_type == "integer"
    assert field.semantic_type is None


def test_parquet_name_protection_retains_bounded_release_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "records.parquet"
    pq.write_table(pa.Table.from_arrays(
        [pa.array([], type=pa.int64()) for _ in _ALIASES], names=list(_ALIASES),
    ), path)

    def reject_rows(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Parquet profiling must use its bounded batch reader")

    monkeypatch.setattr(pq, "read_table", reject_rows)
    for method in ("read", "read_row_group", "read_row_groups", "scan_contents"):
        monkeypatch.setattr(pq.ParquetFile, method, reject_rows)
    original = pq.ParquetFile.iter_batches
    calls: list[int] = []

    def bounded_batches(parquet: Any, *, batch_size: int) -> Any:
        calls.append(batch_size)
        assert batch_size == 256
        return original(parquet, batch_size=batch_size)

    monkeypatch.setattr(pq.ParquetFile, "iter_batches", bounded_batches)

    profile = dataset_profile_from_parquet(path)
    assert calls == [256]
    for field in profile.entity("records").fields:
        assert field.sensitive
        assert field.data_type == "integer"
        assert field.semantic_type is None
        assert field.distribution == {}
