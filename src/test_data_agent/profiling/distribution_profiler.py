"""Distribution profiling without exposing raw PII."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.csv_profiler import (
    mask_pattern,
    numeric_stats,
    parse_bool,
    parse_date_value,
    parse_datetime_value,
    parse_float,
    parse_int,
)

MAX_CATEGORIES = 20


def enrich_distributions(profile: DatasetProfile, rows_by_entity: dict[str, list[dict[str, str]]]) -> DatasetProfile:
    for entity in profile.entities:
        rows = rows_by_entity.get(entity.name, [])
        for field in entity.fields:
            values = [row.get(field.name, "") for row in rows]
            field.distribution = infer_distribution(field, values)
    return profile


def infer_distribution(field: FieldProfile, values: list[str]) -> dict[str, Any]:
    non_null = [value.strip() for value in values if value is not None and value.strip() != ""]
    if field.is_identifier:
        return {"kind": "synthetic_identifier"}
    if field.sensitive:
        patterns = Counter(mask_pattern(value, field.semantic_type) for value in non_null)
        return {"kind": "masked_patterns", "patterns": [{"pattern": pattern, "count": count} for pattern, count in patterns.most_common(10)]}
    if field.data_type == FieldType.INTEGER:
        numbers = sorted(value for value in (parse_int(value) for value in non_null) if value is not None)
        return {"kind": "numeric", **numeric_stats(numbers, integer=True)}
    if field.data_type == FieldType.FLOAT:
        numbers = sorted(value for value in (parse_float(value) for value in non_null) if value is not None)
        return {"kind": "numeric", **numeric_stats(numbers, integer=False)}
    if field.data_type == FieldType.BOOLEAN:
        counts = Counter(parse_bool(value) for value in non_null)
        return {"kind": "boolean", "true_ratio": counts[True] / len(non_null) if non_null else 0.0}
    if field.data_type == FieldType.DATE:
        parsed = sorted(value for value in (parse_date_value(value) for value in non_null) if value is not None)
        return date_distribution(parsed)
    if field.data_type == FieldType.DATETIME:
        parsed = sorted(value for value in (parse_datetime_value(value) for value in non_null) if value is not None)
        return datetime_distribution(parsed)
    counts = Counter(non_null)
    if 0 < len(counts) <= MAX_CATEGORIES:
        return {"kind": "categorical", "categories": [{"value": value, "count": count} for value, count in counts.most_common(MAX_CATEGORIES)]}
    lengths = [len(value) for value in non_null]
    return {"kind": "string_pattern", "min_length": min(lengths, default=1), "max_length": max(lengths, default=12)}


def date_distribution(values: list[date]) -> dict[str, Any]:
    if not values:
        return {"kind": "date_range"}
    return {"kind": "date_range", "min": values[0].isoformat(), "max": values[-1].isoformat()}


def datetime_distribution(values: list[datetime]) -> dict[str, Any]:
    if not values:
        return {"kind": "datetime_range"}
    return {"kind": "datetime_range", "min": values[0].isoformat(), "max": values[-1].isoformat()}
