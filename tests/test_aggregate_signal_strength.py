"""Aggregate adapters preserve risk without promoting weak, incomplete evidence."""

from __future__ import annotations

from typing import Any

import pytest

from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core.field import FieldProfile
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_masking import TrinoMasker, summarize_top_values
from test_data_agent.trino_query_builders import TrinoQuery


def _candidate(kind: str) -> str:
    return {
        "ssn": "".join(("900", "12", "3456")),
        "formatted_ssn": "-".join(("900", "12", "3456")),
        "card": "4242" * 4,
        "entropy": "".join(("aB3dE5fG7hI9", "jK1mN2pQ4rS6", "tU8vW0xYz")),
        "strong": "".join(("sk", "_test_", "51SYNTHETIC")),
    }[kind]


def _legacy_field(
    name: str,
    rows: list[dict[str, Any]],
    *,
    row_count: Any = 100,
    metadata: dict[str, Any] | None = None,
) -> FieldProfile:
    profile = legacy_profile_to_dataset_profile({
        "table": "records",
        "row_count": row_count,
        "columns": [{
            "name": name,
            "data_type": "varchar",
            "approx_distinct_count": len(rows),
            "top_values": rows,
            **(metadata or {}),
        }],
    }, source_type="trino")
    return profile.entity("records").field(name)


def _assert_protected(payload: Any, rows: list[dict[str, Any]]) -> None:
    assert all(str(row["value"]) not in str(payload) for row in rows), (
        "aggregate result exposed a synthetic source spelling"
    )


@pytest.mark.parametrize("kind,name", [
    ("ssn", "quantity"), ("card", "stock_code"), ("entropy", "primary_key"),
])
def test_neutral_weak_aggregate_signals_remain_sensitive_without_semantics(
    kind: str, name: str,
) -> None:
    rows = [{"value": _candidate(kind), "count": 100}]
    summary = summarize_top_values(rows, field_name=name, non_null_count=100)
    field = _legacy_field(name, rows, metadata={"non_null_count": 100})

    assert summary["sensitive"] is field.sensitive is True
    assert summary["semantic_type"] is field.semantic_type is None
    assert summary["masked_patterns"] == [{
        "pattern": f"text_len_{len(_candidate(kind))}", "count": 100,
    }]
    assert field.distribution["patterns"] == summary["masked_patterns"]
    _assert_protected(summary, rows)
    _assert_protected(field.model_dump(), rows)


@pytest.mark.parametrize("kind,name,semantic", [
    ("ssn", "tax_id", "ssn"),
    ("formatted_ssn", "payload", "ssn"),
    ("card", "creditCardNumber", "secret"),
    ("entropy", "access_token", "secret"),
])
@pytest.mark.parametrize("count,expected", [(1, False), (79, False), (80, True)])
def test_aggregate_semantics_use_weighted_full_column_coverage(
    kind: str, name: str, semantic: str, count: int, expected: bool,
) -> None:
    rows = [{"value": _candidate(kind), "count": count}]
    for ordered in (rows, list(reversed(rows))):
        summary = summarize_top_values(ordered, field_name=name, non_null_count=100)
        field = _legacy_field(name, ordered, metadata={"non_null_count": 100})
        assert summary["semantic_type"] == field.semantic_type == (
            semantic if expected else None
        )
        assert summary["sensitive"] is field.sensitive is True
        _assert_protected(summary, rows)
        _assert_protected(field.model_dump(), rows)


def test_aggregate_weighting_and_semantics_are_independent_of_top_value_order() -> None:
    rows = [
        {"value": _candidate("card"), "count": 80},
        {"value": "1234", "count": 20},
    ]
    for ordered in (rows, list(reversed(rows))):
        summary = summarize_top_values(ordered, field_name="card_number", non_null_count=100)
        field = _legacy_field("card_number", ordered, metadata={"non_null_count": 100})
        assert summary["semantic_type"] == field.semantic_type == "secret"
        assert sum(item["count"] for item in summary["masked_patterns"]) == 100
        _assert_protected(summary, rows)
        _assert_protected(field.model_dump(), rows)


@pytest.mark.parametrize("total", [None, "100", 100.0, True, 0, -1, 79])
@pytest.mark.parametrize("kind,name", [
    ("ssn", "ssn"), ("formatted_ssn", "payload"),
    ("card", "card_number"), ("entropy", "password"),
])
def test_unknown_or_invalid_coverage_cannot_grant_aggregate_semantics(
    total: Any, kind: str, name: str,
) -> None:
    rows = [{"value": _candidate(kind), "count": 80}]
    summary = summarize_top_values(rows, field_name=name, non_null_count=total)
    field = _legacy_field(name, rows, metadata={"non_null_count": total})
    assert summary["semantic_type"] is field.semantic_type is None
    assert summary["sensitive"] is field.sensitive is True
    _assert_protected(summary, rows)
    _assert_protected(field.model_dump(), rows)


@pytest.mark.parametrize("count", [None, "80", 80.5, True, 0, -1])
@pytest.mark.parametrize("kind,expected", [("ssn", None), ("strong", "secret")])
def test_malformed_counts_retain_risk_and_only_strong_secret_semantics(
    count: Any, kind: str, expected: str | None,
) -> None:
    rows = [{"value": _candidate(kind), "count": count}]
    summary = summarize_top_values(rows, field_name="ssn", non_null_count=100)
    field = _legacy_field("ssn", rows, metadata={"non_null_count": 100})
    assert summary["semantic_type"] == field.semantic_type == expected
    assert summary["sensitive"] is field.sensitive is True
    assert summary["masked_patterns"][0]["count"] == 0
    _assert_protected(summary, rows)
    _assert_protected(field.model_dump(), rows)


@pytest.mark.parametrize("metadata,expected", [
    ({"non_null_count": 100}, "ssn"),
    ({"null_count": 0}, "ssn"),
    ({"null_ratio": 0.0}, None),
    ({"null_count": 0.0}, None),
    ({"non_null_count": "100", "null_count": 0}, None),
])
def test_legacy_coverage_requires_exact_counts(
    metadata: dict[str, Any], expected: str | None,
) -> None:
    rows = [{"value": _candidate("ssn"), "count": 80}]
    field = _legacy_field("ssn", rows, metadata=metadata)
    assert field.semantic_type == expected
    assert field.sensitive


@pytest.mark.parametrize("null_count,expected", [
    (20, "ssn"), (0, None), (20.0, None), ("20", None), (True, None), (-1, None),
])
def test_legacy_supplied_exact_counts_must_be_consistent(
    null_count: Any, expected: str | None,
) -> None:
    rows = [{"value": _candidate("ssn"), "count": 64}]
    field = _legacy_field("ssn", rows, metadata={
        "non_null_count": 80, "null_count": null_count,
    })
    assert field.semantic_type == expected
    assert field.sensitive


@pytest.mark.parametrize("row_count", ["100", 100.0, True])
def test_legacy_coerced_row_count_cannot_supply_semantic_coverage(row_count: Any) -> None:
    rows = [{"value": _candidate("ssn"), "count": 80}]
    field = _legacy_field("ssn", rows, row_count=row_count, metadata={"null_count": 0})
    assert field.semantic_type is None
    assert field.sensitive


@pytest.mark.parametrize("kind,expected", [("card", "email"), ("strong", "secret")])
def test_legacy_explicit_semantics_are_preserved_except_for_strong_secrets(
    kind: str, expected: str,
) -> None:
    rows = [{"value": _candidate(kind), "count": 100}]
    field = _legacy_field("payload", rows, metadata={
        "non_null_count": 100, "semantic_type": "email",
        "min_value": 1, "max_value": 100,
    })
    assert field.semantic_type == expected
    assert field.sensitive
    assert field.distribution["kind"] == "masked_patterns"
    assert not {"min_value", "max_value"}.intersection(field.distribution)
    _assert_protected(field.model_dump(), rows)


@pytest.mark.parametrize("total,row_count,expected", [
    (100, 100, "ssn"), ("100", 100, None), (100.0, 100, None),
    (True, 100, None), (100, "100", None), (100, 100.0, None),
    (100, True, None), (101, 100, None), (100, -1, None),
])
def test_trino_masker_does_not_coerce_semantic_coverage(
    total: Any, row_count: Any, expected: str | None,
) -> None:
    queries: list[TrinoQuery] = []
    rows = [{"value": _candidate("formatted_ssn"), "count": 80}]

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        if "GROUP BY" in query.sql:
            return rows
        return [{"row_count": row_count, "non_null_count": total, "approx_distinct_count": 1}]

    def reject_sql(sql: str) -> list[dict[str, Any]]:
        raise AssertionError("unexpected SQL execution")

    profile = TrinoMasker(
        config=TrinoConfig(
            host="synthetic.invalid", port=8443, user="synthetic",
            http_scheme="https", allowed_catalogs=frozenset({"analytics"}),
            allowed_schemas=frozenset({"safe_schema"}),
        ),
        fetch_query=fetch_query,
        fetch_sql=reject_sql,
    ).profile_column_safe(
        "analytics", "safe_schema", "records", "payload", "varchar", False, 20,
    )
    assert profile["semantic_type"] == expected
    assert profile["sensitive"]
    assert len(queries) == 2
    _assert_protected(profile, rows)


def test_legacy_invalid_benign_category_weight_has_a_fixed_safe_error() -> None:
    synthetic_marker = "synthetic-malformed-weight"
    with pytest.raises(ValueError, match="^profile category counts must be numeric$") as error:
        _legacy_field("status", [{"value": "ordinary", "count": synthetic_marker}])
    assert synthetic_marker not in str(error.value)
    assert error.value.__cause__ is None


def test_legacy_valid_fractional_category_weights_remain_supported() -> None:
    field = _legacy_field("status", [{"value": "ordinary", "count": 1.5}])
    assert field.distribution["categories"][0]["count"] == 1.5
