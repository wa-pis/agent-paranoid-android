"""Native source scalars cannot bypass conservative CSV-string privacy guards."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from test_data_agent.adapters.csv_file import csv_file_to_dataset_profile
from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core import privacy
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.postgres_profiler import PostgresProfiler
from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.cache import write_cached_profile
from test_data_agent.safety import ProfileSafetyError, SpecSafetyError, assert_profile_safe, assert_spec_safe
from test_data_agent.sql_query_profiling import QueryResultColumn, SqlQueryProfileError, profile_validated_query
from test_data_agent.sql_query_source import (
    QuerySourceColumn,
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    authorize_query_source,
    inspect_query_source,
)
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_masking import TrinoMasker, summarize_top_values


_SOURCE_TYPES = (
    "csv", "csv_folder", "parquet", "postgres", "trino", "postgres_query",
    "trino_query", "json_profile", "legacy_profile", "custom_source",
)


def _candidate(family: str) -> int:
    return int("".join(("900", "12", "3456"))) if family == "ssn" else int("4242" * 4)


def _profile_payload(value: Any, *, name: str = "status", count: Any = 100) -> dict[str, Any]:
    return {"table": "records", "row_count": 100, "columns": [{
        "name": name, "data_type": "bigint", "non_null_count": 100,
        "null_count": 0, "approx_distinct_count": 1,
        "top_values": [{"value": value, "count": count}],
    }]}


@pytest.mark.parametrize("family", ["ssn", "card"])
@pytest.mark.parametrize("representation", ["integer", "string"])
def test_native_numeric_local_categories_are_rejected_like_equivalent_csv_strings(
    family: str, representation: str,
) -> None:
    candidate = _candidate(family)
    value = candidate if representation == "integer" else str(candidate)
    with pytest.raises(ValueError, match="sensitive") as caught:
        privacy.validate_local_category_values(
            field_name="status", semantic_type=None, sensitive=False, values=[value],
        )
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("family", ["ssn", "card"])
@pytest.mark.parametrize("representation", [int, float, Decimal])
def test_profile_source_scalar_classification_does_not_change_the_raw_detector_api(
    family: str, representation: Any,
) -> None:
    value = representation(_candidate(family))
    assert privacy.infer_source_value_signal(value) is not None
    assert privacy.infer_sensitive_value_type(value) is None
    assert privacy.infer_sensitive_value_signal(value) is None


@pytest.mark.parametrize("value", [True, False, 1, 42])
def test_small_business_enum_scalars_remain_allowed(value: Any) -> None:
    privacy.validate_local_category_values(
        field_name="status", semantic_type=None, sensitive=False, values=[value],
    )
    assert privacy.infer_source_value_signal(value) is None


@pytest.mark.parametrize("source_type", _SOURCE_TYPES)
@pytest.mark.parametrize("family", ["ssn", "card"])
def test_every_legacy_source_protects_native_numeric_evidence_without_neutral_semantics(
    source_type: str, family: str,
) -> None:
    candidate = _candidate(family)
    profile = legacy_profile_to_dataset_profile(_profile_payload(candidate), source_type=source_type)
    field = profile.entity("records").field("status")

    assert field.sensitive
    assert field.semantic_type is None
    assert field.data_type.value == "integer"
    assert field.distribution["kind"] == "masked_patterns"
    assert str(candidate) not in profile.model_dump_json()
    assert_profile_safe(profile)


@pytest.mark.parametrize("family,name,semantic", [
    ("ssn", "tax_id", "ssn"), ("card", "card_number", "secret"),
])
@pytest.mark.parametrize("count,expected", [(79, False), (80, True), (None, False), ("80", False)])
def test_native_numeric_semantics_still_require_context_and_valid_full_column_support(
    family: str, name: str, semantic: str, count: Any, expected: bool,
) -> None:
    candidate = _candidate(family)
    profile = legacy_profile_to_dataset_profile(
        _profile_payload(candidate, name=name, count=count), source_type="postgres",
    )
    field = profile.entity("records").field(name)
    summary = summarize_top_values(
        [{"value": str(candidate), "count": count}], field_name=name, non_null_count=100,
    )
    assert field.sensitive and summary["sensitive"]
    assert field.semantic_type == summary["semantic_type"] == (semantic if expected else None)
    assert field.data_type.value == "integer"
    assert str(candidate) not in profile.model_dump_json()
    assert str(candidate) not in str(summary)


@pytest.mark.parametrize("source_type", _SOURCE_TYPES)
@pytest.mark.parametrize("family", ["ssn", "card"])
def test_typed_profiles_reject_native_sensitive_categories_without_echoing_values(
    source_type: str, family: str,
) -> None:
    candidate = _candidate(family)
    profile = DatasetProfile.model_validate({
        "source_type": source_type, "entities": [{
            "name": "records", "row_count": 100, "fields": [{
                "name": "status", "data_type": "integer", "sensitive": False,
                "distribution": {"kind": "categorical", "categories": [{"value": candidate, "count": 100}]},
            }],
        }],
    })
    with pytest.raises(ProfileSafetyError, match="sensitive") as caught:
        assert_profile_safe(profile)
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("family", ["ssn", "card"])
def test_typed_specs_reject_native_sensitive_categories_without_echoing_values(family: str) -> None:
    candidate = _candidate(family)
    spec = DatasetSpec.model_validate({"entities": [{
        "name": "records", "row_count": 100, "fields": [{
            "name": "status", "data_type": "integer", "sensitive": False,
            "distribution": {"kind": "categorical", "categories": [{"value": candidate, "count": 100}]},
        }],
    }]})
    with pytest.raises(SpecSafetyError, match="sensitive") as caught:
        assert_spec_safe(spec)
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("family", ["ssn", "card"])
def test_postgres_native_integer_category_candidates_are_blocked_before_profile_publication(family: str) -> None:
    candidate = _candidate(family)
    config = PostgresConfig(
        source_id="synthetic", host="synthetic.invalid", port=5432, database="synthetic",
        user="synthetic", password_env=None, allowed_schemas=frozenset(("public",)),
        allowed_tables=frozenset(("public.records",)), allowed_columns=frozenset(("public.records.status",)),
    )
    queries = []

    def fetch(query: Any) -> list[dict[str, object]]:
        queries.append(query)
        if "pg_catalog.format_type" in query.sql:
            return [{"column_name": "status", "data_type": "bigint", "is_nullable": False, "ordinal_position": 1}]
        if "c.relkind IN ('r', 'p')" in query.sql:
            return [{"table_schema": "public", "table_name": "records"}]
        if "pg_catalog.pg_constraint" in query.sql:
            return []
        if "GROUP BY" in query.sql:
            return [{"value": candidate, "count": 100}]
        if "non_null_count" in query.sql:
            return [{
                "row_count": 100, "non_null_count": 100, "distinct_count": 1,
                "max_abs_magnitude": 8, "has_negative": False, "has_positive": True,
            }]
        if query.sql.startswith("SELECT count(*) AS row_count FROM"):
            return [{"row_count": 100}]
        raise AssertionError("unexpected PostgreSQL query after unsafe category evidence")

    with pytest.raises(ValueError, match="sensitive") as caught:
        PostgresProfiler(config, fetch).profile(local_category_fields=(
            privacy.LocalCategoryField(entity="synthetic.public.records", field="status"),
        ))
    assert len(queries) == 6
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("family", ["ssn", "card"])
def test_query_native_integer_category_candidates_are_blocked_without_returning_rows(
    tmp_path: Path, adapter: SqlQueryAdapter, family: str,
) -> None:
    candidate = _candidate(family)
    table = "public.records" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.records"
    path = tmp_path / "query.sql"
    path.write_text(f"SELECT status FROM {table}", encoding="utf-8")
    plan = authorize_query_source(
        inspect_query_source(SqlQueryProfileRequest(adapter, "synthetic", "records", path)),
        (QuerySourceColumn("status", "bigint", False),),
    )
    queries = []

    def describe(query: Any) -> tuple[QueryResultColumn, ...]:
        queries.append(query)
        assert "WHERE FALSE" in query.sql
        return (QueryResultColumn("status", "bigint", False),)

    def fetch(query: Any) -> list[dict[str, object]]:
        queries.append(query)
        if "GROUP BY" in query.sql:
            return [{"value": candidate, "count": 100}]
        if "non_null_count" in query.sql:
            return [{
                "row_count": 100, "non_null_count": 100, "distinct_count": 1,
                "max_abs_magnitude": 8, "has_negative": False, "has_positive": True,
            }]
        return [{"row_count": 100}]

    with pytest.raises(SqlQueryProfileError) as caught:
        profile_validated_query(
            plan, describe_query=describe, fetch_query=fetch,
            local_category_fields=(privacy.LocalCategoryField(entity=plan.entity_name, field="status"),),
        )
    assert len(queries) == 4
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("source_type", _SOURCE_TYPES)
@pytest.mark.parametrize("family", ["ssn", "card"])
def test_native_sensitive_numeric_summaries_are_protected_for_every_legacy_source(
    source_type: str, family: str,
) -> None:
    candidate = _candidate(family)
    payload = _profile_payload(candidate)
    del payload["columns"][0]["top_values"]
    payload["columns"][0].update({"min_value": candidate, "max_value": candidate})
    profile = legacy_profile_to_dataset_profile(payload, source_type=source_type)
    field = profile.entity("records").field("status")

    assert field.sensitive
    assert field.semantic_type is None
    assert field.data_type.value == "integer"
    assert str(candidate) not in profile.model_dump_json()
    assert_profile_safe(profile)

    untrusted = DatasetProfile.model_validate({
        "source_type": source_type, "entities": [{
            "name": "records", "row_count": 100, "fields": [{
                "name": "status", "data_type": "integer", "sensitive": False,
                "distribution": {"kind": "numeric", "min_value": candidate, "max_value": candidate},
            }],
        }],
    })
    with pytest.raises(ProfileSafetyError, match="sensitive") as caught:
        assert_profile_safe(untrusted)
    assert str(candidate) not in str(caught.value)


@pytest.mark.parametrize("use_cache", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_csv_folder_suppresses_sensitive_derived_quantiles_like_single_csv(
    tmp_path: Path, use_cache: bool, reverse: bool,
) -> None:
    values = ["123.45", "456.78"]
    assert all(privacy.infer_source_value_signal(value) is None for value in values)
    source = tmp_path / "source"
    source.mkdir()
    path = source / "items.csv"
    path.write_text("quantity\n" + "\n".join(reversed(values) if reverse else values) + "\n")
    cache_dir = tmp_path / "cache"

    single = csv_file_to_dataset_profile(path)
    folder = profile_example_folder(source, cache_dir=cache_dir, use_cache=use_cache)
    if use_cache:
        cached = profile_example_folder(source, cache_dir=cache_dir)
        assert cached == folder
    single_field = single.entity("items").field("quantity")
    folder_field = folder.entity("items").field("quantity")

    assert single_field.sensitive and folder_field.sensitive
    assert single_field.semantic_type is folder_field.semantic_type is None
    assert single_field.distribution == folder_field.distribution == {}
    assert all(value not in folder.model_dump_json() for value in values)
    assert_profile_safe(folder)
    assert_spec_safe(infer_dataset_spec(folder, count=2))


@pytest.mark.parametrize("previous_version", [10, 11])
def test_csv_folder_rebuilds_previous_cache_with_sensitive_derived_quantiles(
    tmp_path: Path, previous_version: int,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "items.csv").write_text("quantity\n123.45\n456.78\n")
    cache_dir = tmp_path / "cache"
    previous = profile_example_folder(source, use_cache=False)
    previous_field = previous.entity("items").field("quantity")
    previous_field.sensitive = False
    previous_field.distribution = {
        "kind": "numeric", "min_value": 123.45, "max_value": 456.78,
        "p05": 140.1165, "p95": 440.1135,
    }
    cache_path = write_cached_profile(source, previous, cache_dir=cache_dir)
    cached_payload = json.loads(cache_path.read_text())
    cached_payload["format_version"] = previous_version
    cache_path.write_text(json.dumps(cached_payload))

    rebuilt = profile_example_folder(source, cache_dir=cache_dir)

    assert rebuilt.entity("items").field("quantity").sensitive
    assert rebuilt.entity("items").field("quantity").distribution == {}
    assert_profile_safe(rebuilt)
    assert_spec_safe(infer_dataset_spec(rebuilt, count=2))
    assert json.loads(cache_path.read_text())["format_version"] == 12


@pytest.mark.parametrize("family", ["ssn", "card"])
def test_trino_neutral_numeric_summaries_trigger_sensitivity_without_extra_queries(family: str) -> None:
    candidate = _candidate(family)
    queries = []

    def fetch(query: Any) -> list[dict[str, Any]]:
        queries.append(query)
        return [{
            "row_count": 100, "non_null_count": 100, "approx_distinct_count": 1,
            "min_value": candidate, "max_value": candidate, "p05": candidate, "p95": candidate,
        }]

    def reject_sql(sql: str) -> list[dict[str, Any]]:
        raise AssertionError("unexpected row access")

    profile = TrinoMasker(
        config=TrinoConfig(
            host="synthetic.invalid", port=8443, user="synthetic", http_scheme="https",
            allowed_catalogs=frozenset(("lake",)), allowed_schemas=frozenset(("safe",)),
        ), fetch_query=fetch, fetch_sql=reject_sql,
    ).profile_column_safe("lake", "safe", "records", "status", "bigint", False, 20)

    assert profile["sensitive"]
    assert profile.get("semantic_type") is None
    assert not {"min_value", "max_value", "p05", "p95"}.intersection(profile)
    assert str(candidate) not in str(profile)
    assert len(queries) == 1
