"""Aggregate-only profiling for validated SQL query sources."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.privacy import (
    LocalCategoryField,
    infer_sensitive_from_name,
    validate_local_category_values,
)
from test_data_agent.profile_types import ProfileDataType, coerce_profile_type
from test_data_agent.sql_query_source import (
    QUERY_SOURCE_POLICY_VERSION,
    SqlQueryAdapter,
    ValidatedSqlQuery,
)


class SqlQueryProfileError(RuntimeError):
    """A source-free query profiling failure."""


@dataclass(frozen=True, slots=True)
class TrustedProfileQuery:
    sql: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class QueryResultColumn:
    name: str
    data_type: str
    nullable: bool = True


QueryFetcher = Callable[[TrustedProfileQuery], list[dict[str, object]]]
QueryDescriber = Callable[[TrustedProfileQuery], Sequence[QueryResultColumn]]


def profile_validated_query(
    plan: ValidatedSqlQuery,
    *,
    describe_query: QueryDescriber,
    fetch_query: QueryFetcher,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> DatasetProfile:
    """Build one source-free profile without fetching the derived rows."""

    try:
        columns = _complete_schema(
            plan,
            describe_query(build_no_row_schema_query(plan)),
        )
        row_count = _non_negative_int(
            _single_row(fetch_query(build_query_row_count_query(plan))).get(
                "row_count"
            ),
            "row count",
        )
        categories = _local_categories(plan, columns, local_category_fields)
        profile_columns = [
            _profile_column(
                plan,
                column,
                row_count,
                fetch_query,
                categories.get(column.name),
            )
            for column in columns
        ]
        profile = legacy_profile_to_dataset_profile(
            {
                "table": plan.entity_name,
                "row_count": row_count,
                "columns": profile_columns,
                "local_category_fields": list(categories.values()),
            },
            source_type=f"{plan.adapter.value}_query",
        )
        return profile.model_copy(
            update={
                "source_fingerprint": plan.fingerprint,
                "source_policy_version": QUERY_SOURCE_POLICY_VERSION,
            }
        )
    except SqlQueryProfileError:
        raise
    except Exception:
        raise SqlQueryProfileError("SQL query source profiling failed") from None


def build_no_row_schema_query(plan: ValidatedSqlQuery) -> TrustedProfileQuery:
    fields = ", ".join(_quote_identifier(name) for name in plan.output_fields)
    return TrustedProfileQuery(
        f"SELECT {fields} FROM ({plan.sql}) AS \"__apa_source\" WHERE FALSE"
    )


def build_query_row_count_query(plan: ValidatedSqlQuery) -> TrustedProfileQuery:
    return TrustedProfileQuery(
        f"SELECT count(*) AS row_count FROM ({plan.sql}) AS \"__apa_source\""
    )


def build_query_column_summary_query(
    plan: ValidatedSqlQuery,
    column: str,
) -> TrustedProfileQuery:
    safe = _allowed_output_column(plan, column)
    return TrustedProfileQuery(
        f"SELECT count(*) AS row_count, count({safe}) AS non_null_count, "
        f"count(DISTINCT {safe}) AS distinct_count "
        f"FROM ({plan.sql}) AS \"__apa_source\""
    )


def build_query_numeric_shape_query(
    plan: ValidatedSqlQuery,
    column: str,
) -> TrustedProfileQuery:
    safe = _allowed_output_column(plan, column)
    if plan.adapter is SqlQueryAdapter.POSTGRES:
        magnitude = f"floor(log(10, abs(CAST({safe} AS numeric))))::integer"
        negative = f"bool_or({safe} < 0)"
        positive = f"bool_or({safe} > 0)"
    else:
        magnitude = f"CAST(floor(log10(abs(CAST({safe} AS double)))) AS integer)"
        negative = f"bool_or({safe} < 0)"
        positive = f"bool_or({safe} > 0)"
    return TrustedProfileQuery(
        f"SELECT count(*) AS row_count, count({safe}) AS non_null_count, "
        f"count(DISTINCT {safe}) AS distinct_count, "
        f"{negative} AS has_negative, {positive} AS has_positive, "
        f"max(CASE WHEN {safe} = 0 THEN NULL ELSE {magnitude} END) "
        "AS max_abs_magnitude "
        f"FROM ({plan.sql}) AS \"__apa_source\""
    )


def build_query_local_category_query(
    plan: ValidatedSqlQuery,
    column: str,
    *,
    max_categories: int = 20,
) -> TrustedProfileQuery:
    if max_categories < 1 or max_categories > 100:
        raise SqlQueryProfileError("SQL query category budget is invalid")
    safe = _allowed_output_column(plan, column)
    return TrustedProfileQuery(
        f"SELECT {safe} AS value, count(*) AS count "
        f"FROM ({plan.sql}) AS \"__apa_source\" "
        f"WHERE {safe} IS NOT NULL GROUP BY {safe} "
        f"ORDER BY count DESC, value ASC LIMIT {max_categories + 1}"
    )


def _complete_schema(
    plan: ValidatedSqlQuery,
    rows: Sequence[QueryResultColumn],
) -> tuple[QueryResultColumn, ...]:
    if tuple(column.name for column in rows) != plan.output_fields:
        raise SqlQueryProfileError("SQL query schema metadata is incomplete")
    if len({column.name for column in rows}) != len(rows):
        raise SqlQueryProfileError("SQL query schema metadata is invalid")
    for column in rows:
        if not _supported_scalar_type(column.data_type):
            raise SqlQueryProfileError("SQL query output type is unsupported")
    return tuple(rows)


def _local_categories(
    plan: ValidatedSqlQuery,
    columns: Sequence[QueryResultColumn],
    requested: Sequence[LocalCategoryField],
) -> dict[str, LocalCategoryField]:
    names = {column.name for column in columns}
    selected: dict[str, LocalCategoryField] = {}
    for category_field in requested:
        if (
            category_field.entity != plan.entity_name
            or category_field.field not in names
        ):
            raise SqlQueryProfileError(
                "SQL query local category field is outside the exact output allowlist"
            )
        if category_field.field in selected or infer_sensitive_from_name(
            category_field.field
        ):
            raise SqlQueryProfileError("SQL query local category field is not allowed")
        selected[category_field.field] = category_field
    return selected


def _profile_column(
    plan: ValidatedSqlQuery,
    column: QueryResultColumn,
    row_count: int,
    fetch_query: QueryFetcher,
    local_category_field: LocalCategoryField | None,
) -> dict[str, object]:
    summary = _single_row(
        fetch_query(build_query_column_summary_query(plan, column.name))
    )
    summary_row_count = _non_negative_int(summary.get("row_count"), "row count")
    non_null_count = _non_negative_int(
        summary.get("non_null_count"), "non-null count"
    )
    distinct_count = _non_negative_int(
        summary.get("distinct_count"), "distinct count"
    )
    if (
        summary_row_count != row_count
        or non_null_count > row_count
        or distinct_count > non_null_count
    ):
        raise SqlQueryProfileError("SQL query aggregate counts are invalid")
    result: dict[str, object] = {
        "name": column.name,
        "data_type": column.data_type,
        "nullable": column.nullable,
        "null_ratio": (row_count - non_null_count) / row_count if row_count else 0.0,
        "approx_distinct_count": distinct_count,
    }
    if coerce_profile_type(column.data_type) in {
        ProfileDataType.INTEGER,
        ProfileDataType.FLOAT,
    }:
        shape = _single_row(
            fetch_query(build_query_numeric_shape_query(plan, column.name))
        )
        if (
            _non_negative_int(shape.get("row_count"), "numeric row count")
            != row_count
            or _non_negative_int(
                shape.get("non_null_count"), "numeric non-null count"
            )
            != non_null_count
            or _non_negative_int(
                shape.get("distinct_count"), "numeric distinct count"
            )
            != distinct_count
        ):
            raise SqlQueryProfileError("SQL query numeric aggregates are invalid")
        has_negative = _as_bool(shape.get("has_negative"))
        has_positive = _as_bool(shape.get("has_positive"))
        magnitude = shape.get("max_abs_magnitude")
        if magnitude is not None and (has_negative or has_positive):
            result["numeric_shape"] = {
                "max_abs_magnitude": _bounded_magnitude(magnitude),
                "has_negative": has_negative,
                "has_positive": has_positive,
            }
    if local_category_field is not None:
        category_rows = fetch_query(
            build_query_local_category_query(plan, column.name)
        )
        values = [row.get("value") for row in category_rows]
        validate_local_category_values(
            field_name=column.name,
            semantic_type=None,
            sensitive=False,
            values=values,
        )
        counts = [_positive_int(row.get("count"), "category count") for row in category_rows]
        if len(values) != distinct_count or sum(counts) != non_null_count:
            raise SqlQueryProfileError("SQL query local category aggregate is incomplete")
        result["top_values"] = [
            {"value": value, "count": count}
            for value, count in zip(values, counts, strict=True)
        ]
    return result


def _supported_scalar_type(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return bool(
        re.fullmatch(
            r"(?:tinyint|smallint|integer|bigint|real|double(?: precision)?|"
            r"boolean|date|text|string|uuid|"
            r"(?:decimal|numeric)(?:\(\d+(?:,\s*\d+)?\))?|"
            r"(?:varchar|char|character varying|character)(?:\(\d+\))?|"
            r"timestamp(?:\(\d+\))?(?: with(?:out)? time zone)?)",
            normalized,
        )
    )


def _allowed_output_column(plan: ValidatedSqlQuery, column: str) -> str:
    if column not in plan.output_fields:
        raise SqlQueryProfileError("SQL query output column is not allowed")
    return _quote_identifier(column)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _single_row(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    if len(rows) != 1:
        raise SqlQueryProfileError("SQL query aggregate result is incomplete")
    return rows[0]


def _non_negative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise SqlQueryProfileError(f"SQL query {label} is invalid")
    return value


def _positive_int(value: object, label: str) -> int:
    result = _non_negative_int(value, label)
    if result == 0:
        raise SqlQueryProfileError(f"SQL query {label} is invalid")
    return result


def _as_bool(value: object) -> bool:
    if type(value) is bool:
        return value
    if value is None:
        return False
    raise SqlQueryProfileError("SQL query boolean aggregate is invalid")


def _bounded_magnitude(value: object) -> int:
    if type(value) is not int or not -308 <= value <= 307:
        raise SqlQueryProfileError("SQL query numeric magnitude is invalid")
    return value


__all__ = [
    "QueryResultColumn",
    "SqlQueryProfileError",
    "TrustedProfileQuery",
    "build_no_row_schema_query",
    "build_query_column_summary_query",
    "build_query_local_category_query",
    "build_query_numeric_shape_query",
    "build_query_row_count_query",
    "profile_validated_query",
]
