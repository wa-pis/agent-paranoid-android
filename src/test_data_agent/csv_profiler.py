"""Safe CSV profiling for synthetic data generation.

The profiler only emits schema, aggregates, distributions, and masked patterns.
It never includes raw values for likely PII columns.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.core.privacy import infer_sensitive_from_name, mask_pattern, semantic_type_is_sensitive
from test_data_agent.spec import DataType, infer_profile_data_type


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
SSN_RE = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")
MAX_ENUM_VALUES = 20


class CSVColumnProfile(BaseModel):
    name: str
    data_type: str
    nullable: bool
    null_count: int
    null_ratio: float
    approx_distinct_count: int
    sensitive: bool
    semantic_type: str | None = None
    top_values: list[dict[str, Any]] = Field(default_factory=list)
    masked_patterns: list[dict[str, Any]] = Field(default_factory=list)
    min_value: int | float | str | None = None
    max_value: int | float | str | None = None
    p05: int | float | None = None
    p95: int | float | None = None
    min_date: str | None = None
    max_date: str | None = None
    min_timestamp: str | None = None
    max_timestamp: str | None = None


class CSVProfile(BaseModel):
    source_type: str = "csv"
    table: str
    row_count: int
    columns: list[CSVColumnProfile]


def profile_csv(path: Path, table_name: str | None = None) -> CSVProfile:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header row")
        columns = {name: [] for name in reader.fieldnames}
        for row in reader:
            for name in reader.fieldnames:
                columns[name].append(row.get(name, ""))

    row_count = len(next(iter(columns.values()), []))
    return CSVProfile(
        table=table_name or path.stem,
        row_count=row_count,
        columns=[profile_column(name, values, row_count) for name, values in columns.items()],
    )


def profile_column(name: str, values: list[str], row_count: int) -> CSVColumnProfile:
    non_null = [value.strip() for value in values if value is not None and value.strip() != ""]
    null_count = row_count - len(non_null)
    semantic_type = infer_semantic_type(name, non_null)
    base_type = infer_data_type(name, non_null, semantic_type)
    sensitive = infer_sensitive_from_name(name) or semantic_type_is_sensitive(semantic_type)
    counts = Counter(non_null)

    top_values: list[dict[str, Any]] = []
    masked_patterns: list[dict[str, Any]] = []
    if sensitive:
        masked_patterns = [
            {"pattern": pattern, "count": count}
            for pattern, count in Counter(mask_pattern(value, semantic_type) for value in non_null).most_common(10)
        ]
    elif base_type == DataType.STRING and 0 < len(counts) <= MAX_ENUM_VALUES:
        top_values = [{"value": value, "count": count} for value, count in counts.most_common(MAX_ENUM_VALUES)]

    stats = range_stats(non_null, base_type)
    return CSVColumnProfile(
        name=name,
        data_type=base_type.value,
        nullable=null_count > 0,
        null_count=null_count,
        null_ratio=round(null_count / row_count, 6) if row_count else 0.0,
        approx_distinct_count=len(counts),
        sensitive=sensitive,
        semantic_type=semantic_type,
        top_values=top_values,
        masked_patterns=masked_patterns,
        **stats,
    )


def infer_semantic_type(name: str, values: list[str]) -> str | None:
    lowered = name.lower()
    if "email" in lowered or "mail" in lowered:
        return "email"
    if "phone" in lowered:
        return "phone"
    if "ssn" in lowered or "tax_id" in lowered:
        return "ssn"
    sample = values[:100]
    if sample and sum(bool(EMAIL_RE.fullmatch(value)) for value in sample) / len(sample) >= 0.8:
        return "email"
    if sample and sum(bool(SSN_RE.fullmatch(value)) for value in sample) / len(sample) >= 0.8:
        return "ssn"
    if sample and sum(bool(PHONE_RE.fullmatch(value)) for value in sample) / len(sample) >= 0.8:
        return "phone"
    return None


def infer_data_type(name: str, values: list[str], semantic_type: str | None) -> DataType:
    if semantic_type == "email":
        return DataType.EMAIL
    if semantic_type == "phone":
        return DataType.PHONE
    profile_hint = infer_profile_data_type({"name": name, "data_type": "string", "semantic_type": semantic_type})
    if profile_hint != DataType.STRING:
        return profile_hint
    if not values:
        return DataType.STRING
    if all(parse_int(value) is not None for value in values):
        return DataType.INTEGER
    if all(parse_float(value) is not None for value in values):
        return DataType.FLOAT
    if all(parse_bool(value) is not None for value in values):
        return DataType.BOOLEAN
    if all(parse_datetime_value(value) is not None for value in values):
        return DataType.DATETIME
    if all(parse_date_value(value) is not None for value in values):
        return DataType.DATE
    return DataType.STRING


def range_stats(values: list[str], data_type: DataType) -> dict[str, Any]:
    if not values:
        return {}
    if data_type == DataType.INTEGER:
        numbers = sorted(parse_int(value) for value in values)
        return numeric_stats([number for number in numbers if number is not None], integer=True)
    if data_type == DataType.FLOAT:
        numbers = sorted(parse_float(value) for value in values)
        return numeric_stats([number for number in numbers if number is not None], integer=False)
    if data_type == DataType.DATE:
        dates = sorted(parse_date_value(value) for value in values)
        parsed = [item for item in dates if item is not None]
        return {"min_date": parsed[0].isoformat(), "max_date": parsed[-1].isoformat()} if parsed else {}
    if data_type == DataType.DATETIME:
        datetimes = sorted(parse_datetime_value(value) for value in values)
        parsed = [item for item in datetimes if item is not None]
        return {"min_timestamp": parsed[0].isoformat(), "max_timestamp": parsed[-1].isoformat()} if parsed else {}
    return {}


def numeric_stats(numbers: list[int | float], integer: bool) -> dict[str, Any]:
    if not numbers:
        return {}
    stats: dict[str, Any] = {
        "min_value": numbers[0],
        "max_value": numbers[-1],
        "p05": percentile(numbers, 0.05),
        "p95": percentile(numbers, 0.95),
    }
    if integer:
        stats = {key: int(round(value)) for key, value in stats.items()}
    return stats


def percentile(numbers: list[int | float], ratio: float) -> float:
    if len(numbers) == 1:
        return float(numbers[0])
    index = ratio * (len(numbers) - 1)
    lower = int(index)
    upper = min(lower + 1, len(numbers) - 1)
    weight = index - lower
    return float(numbers[lower] * (1 - weight) + numbers[upper] * weight)


def parse_int(value: str) -> int | None:
    try:
        if value.strip() != str(int(value)):
            return None
        return int(value)
    except ValueError:
        return None


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_bool(value: str) -> bool | None:
    lowered = value.lower()
    if lowered in {"true", "t", "1", "yes", "y"}:
        return True
    if lowered in {"false", "f", "0", "no", "n"}:
        return False
    return None


def parse_date_value(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_datetime_value(value: str) -> datetime | None:
    if "T" not in value and " " not in value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
