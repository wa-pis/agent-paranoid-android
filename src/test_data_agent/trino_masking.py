"""Transport-neutral masking and safe Trino category summaries."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from test_data_agent.core.privacy import (
    infer_sensitive_from_name as infer_sensitive_from_name,
    infer_sensitive_type_from_values as infer_sensitive_type_from_values,
    infer_sensitive_value_type as infer_sensitive_value_type,
    looks_sensitive_value as looks_sensitive_value,
    mask_pattern as mask_pattern,
    mask_value as mask_value,
    synthetic_category_distribution as synthetic_category_distribution,
)
from test_data_agent.core.limits import InputLimitError, max_input_cells, max_json_depth
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_query_builders import (
    TrinoQuery,
    build_column_cardinality_query,
    build_column_profile_query,
    build_sensitive_numeric_shape_query,
    build_top_values_query,
    is_numeric_trino_type,
    is_string_trino_type,
)
from test_data_agent.trino_sql_policy import check_allowlist, validate_safe_select

QueryFetcher = Callable[[TrinoQuery], list[dict[str, Any]]]
SqlFetcher = Callable[[str], list[dict[str, Any]]]


def mask_row(row: dict[str, Any]) -> dict[str, Any]:
    """Mask likely PII or secret values while retaining safe aggregate fields."""
    return {
        key: mask_value(value)
        if infer_sensitive_from_name(key) or looks_sensitive_value(value)
        else value
        for key, value in row.items()
    }


def _mask_returned_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mask nested strings on the bounded explicit row-returning surface."""
    remaining = [max_input_cells()]
    depth_limit = max_json_depth()
    return [
        {
            key: _mask_returned_value(
                value,
                key=key,
                depth=1,
                depth_limit=depth_limit,
                remaining=remaining,
            )
            for key, value in row.items()
        }
        for row in rows
    ]


def _mask_returned_value(
    value: Any,
    *,
    key: str,
    depth: int,
    depth_limit: int,
    remaining: list[int],
) -> Any:
    remaining[0] -= 1
    if remaining[0] < 0:
        raise InputLimitError("Trino safe-select result contains too many values")
    if depth > depth_limit:
        raise InputLimitError(
            f"Trino safe-select result values must have depth <= {depth_limit}"
        )
    if (
        isinstance(value, str)
        or infer_sensitive_from_name(key)
        or looks_sensitive_value(value)
    ):
        return mask_value(value)
    if isinstance(value, dict):
        return {
            nested_key: _mask_returned_value(
                nested,
                key=str(nested_key),
                depth=depth + 1,
                depth_limit=depth_limit,
                remaining=remaining,
            )
            for nested_key, nested in value.items()
        }
    if isinstance(value, (list, tuple)):
        container_type = tuple if isinstance(value, tuple) else list
        return container_type(
            _mask_returned_value(
                nested,
                key="",
                depth=depth + 1,
                depth_limit=depth_limit,
                remaining=remaining,
            )
            for nested in value
        )
    return value


def summarize_top_values(top_values: list[dict[str, Any]]) -> dict[str, Any]:
    """Replace source categories with masked patterns or synthetic rank labels."""
    content_sensitive_type = infer_sensitive_type_from_values(
        row.get("value") for row in top_values
    )
    if content_sensitive_type is None:
        return {
            "top_values": synthetic_category_distribution(
                int(row.get("count") or 0) for row in top_values
            )
        }

    pattern_counts: Counter[str] = Counter()
    for row in top_values:
        value = row.get("value")
        value_type = infer_sensitive_value_type(value) or content_sensitive_type
        pattern_counts[mask_pattern(str(value), value_type)] += int(
            row.get("count") or 0
        )
    return {
        "sensitive": True,
        "semantic_type": content_sensitive_type,
        "masked_patterns": [
            {"pattern": pattern, "count": count}
            for pattern, count in pattern_counts.most_common(10)
        ],
    }


@dataclass(frozen=True)
class TrinoMasker:
    """Apply masking below transports with explicit policy and query ports."""

    config: TrinoConfig
    fetch_query: QueryFetcher
    fetch_sql: SqlFetcher

    def profile_column_safe(
        self,
        catalog: str,
        schema: str,
        table: str,
        column: str,
        data_type: str,
        nullable: bool,
        max_top_values: int,
    ) -> dict[str, Any]:
        check_allowlist(catalog=catalog, schema=schema, config=self.config)
        sensitive = infer_sensitive_from_name(column)
        sensitive_numeric = sensitive and is_numeric_trino_type(data_type)
        aggregate_rows = self.fetch_query(
            build_sensitive_numeric_shape_query(catalog, schema, table, column)
            if sensitive_numeric
            else (
                build_column_cardinality_query(catalog, schema, table, column)
                if sensitive
                else build_column_profile_query(
                    catalog, schema, table, column, data_type
                )
            )
        )
        aggregates = aggregate_rows[0] if aggregate_rows else {}
        row_count = int(aggregates.get("row_count") or 0)
        non_null_count = int(aggregates.get("non_null_count") or 0)
        profile: dict[str, Any] = {
            "name": column,
            "data_type": data_type,
            "nullable": nullable,
            "row_count": row_count,
            "null_count": max(0, row_count - non_null_count),
            "null_ratio": round((row_count - non_null_count) / row_count, 6)
            if row_count
            else 0.0,
            "approx_distinct_count": aggregates.get("approx_distinct_count", 0),
            "sensitive": sensitive,
        }
        profile.update(
            {
                key: value
                for key, value in aggregates.items()
                if key not in profile
                and key
                not in {"max_abs_magnitude", "has_negative", "has_positive"}
                and value is not None
            }
        )
        if sensitive_numeric and aggregates.get("max_abs_magnitude") is not None:
            profile["numeric_shape"] = {
                "max_abs_magnitude": int(aggregates["max_abs_magnitude"]),
                "has_negative": bool(aggregates.get("has_negative", False)),
                "has_positive": bool(aggregates.get("has_positive", False)),
            }
        approx_distinct = int(profile.get("approx_distinct_count") or 0)
        if (
            is_string_trino_type(data_type)
            and not sensitive
            and 0 < approx_distinct <= max_top_values
        ):
            can_return_categories = (
                self.config.allowed_table_columns is None
                or _is_table_column_allowlisted(
                    self.config, catalog, schema, table, column
                )
            )
            if can_return_categories:
                top_values = self.fetch_query(
                    build_top_values_query(
                        catalog,
                        schema,
                        table,
                        column,
                        max_top_values,
                    )
                )
                profile.update(summarize_top_values(top_values))
        return profile

    def run_safe_select(self, sql: str) -> list[dict[str, Any]]:
        safe_sql = validate_safe_select(sql, require_limit=True, config=self.config)
        return _mask_returned_rows(self.fetch_sql(safe_sql))


def _is_table_column_allowlisted(
    config: TrinoConfig,
    catalog: str,
    schema: str,
    table: str,
    column: str,
) -> bool:
    if config.allowed_table_columns is None:
        return True
    return (
        f"{catalog}.{schema}.{table}.{column}" in config.allowed_table_columns
    )
