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
MAX_TRACKED_DISTINCT_VALUES = 1_000
MAX_NUMERIC_SAMPLE_VALUES = 10_000
CSV_SAMPLE_BYTES = 8192


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
    encoding = detect_csv_encoding(path)
    sample = read_csv_sample(path, encoding)
    dialect = detect_csv_dialect(sample)
    with path.open(newline="", encoding=encoding) as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header row")
        accumulators = {name: CSVColumnAccumulator(name) for name in reader.fieldnames}
        row_count = 0
        for row in reader:
            row_count += 1
            for name in reader.fieldnames:
                accumulators[name].add(row.get(name, ""))
    return CSVProfile(
        table=table_name or path.stem,
        row_count=row_count,
        columns=[accumulator.to_profile(row_count) for accumulator in accumulators.values()],
    )


def detect_csv_encoding(path: Path) -> str:
    with path.open("rb") as handle:
        raw = handle.read(CSV_SAMPLE_BYTES)
    try:
        raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return "latin-1"
    return "utf-8-sig"


def read_csv_sample(path: Path, encoding: str) -> str:
    with path.open("rb") as handle:
        return handle.read(CSV_SAMPLE_BYTES).decode(encoding, errors="replace")


def detect_csv_dialect(text: str) -> csv.Dialect:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


class CSVColumnAccumulator:
    def __init__(self, name: str) -> None:
        self.name = name
        self.non_null_count = 0
        self.semantic_sample: list[str] = []
        self.counts: Counter[str] = Counter()
        self.distinct_overflow = False
        self.integer_values: list[int] = []
        self.float_values: list[float] = []
        self.date_values: list[date] = []
        self.datetime_values: list[datetime] = []
        self.all_int = True
        self.all_float = True
        self.all_bool = True
        self.all_datetime = True
        self.all_date = True

    def add(self, raw_value: str | None) -> None:
        value = raw_value.strip() if raw_value is not None else ""
        if value == "":
            return
        self.non_null_count += 1
        if len(self.semantic_sample) < 100:
            self.semantic_sample.append(value)
        self.add_count(value)
        self.add_typed_samples(value)

    def add_count(self, value: str) -> None:
        if value in self.counts:
            self.counts[value] += 1
            return
        if len(self.counts) < MAX_TRACKED_DISTINCT_VALUES:
            self.counts[value] = 1
            return
        self.distinct_overflow = True

    def add_typed_samples(self, value: str) -> None:
        parsed_int = parse_int(value)
        if parsed_int is None:
            self.all_int = False
        elif len(self.integer_values) < MAX_NUMERIC_SAMPLE_VALUES:
            self.integer_values.append(parsed_int)

        parsed_float = parse_float(value)
        if parsed_float is None:
            self.all_float = False
        elif len(self.float_values) < MAX_NUMERIC_SAMPLE_VALUES:
            self.float_values.append(parsed_float)

        if parse_bool(value) is None:
            self.all_bool = False

        parsed_datetime = parse_datetime_value(value)
        if parsed_datetime is None:
            self.all_datetime = False
        elif len(self.datetime_values) < MAX_NUMERIC_SAMPLE_VALUES:
            self.datetime_values.append(parsed_datetime)

        parsed_date = parse_date_value(value)
        if parsed_date is None:
            self.all_date = False
        elif len(self.date_values) < MAX_NUMERIC_SAMPLE_VALUES:
            self.date_values.append(parsed_date)

    def to_profile(self, row_count: int) -> CSVColumnProfile:
        null_count = row_count - self.non_null_count
        semantic_type = infer_semantic_type(self.name, self.semantic_sample)
        base_type = self.infer_data_type(semantic_type)
        sensitive = infer_sensitive_from_name(self.name) or semantic_type_is_sensitive(semantic_type)
        top_values: list[dict[str, Any]] = []
        masked_patterns: list[dict[str, Any]] = []
        if sensitive:
            pattern_counts: Counter[str] = Counter()
            for value, count in self.counts.items():
                pattern_counts[mask_pattern(value, semantic_type)] += count
            masked_patterns = [{"pattern": pattern, "count": count} for pattern, count in pattern_counts.most_common(10)]
        elif (
            base_type == DataType.STRING
            and not self.distinct_overflow
            and 0 < len(self.counts) <= MAX_ENUM_VALUES
        ):
            top_values = [
                {"value": value, "count": count}
                for value, count in self.counts.most_common(MAX_ENUM_VALUES)
            ]
        return CSVColumnProfile(
            name=self.name,
            data_type=base_type.value,
            nullable=null_count > 0,
            null_count=null_count,
            null_ratio=round(null_count / row_count, 6) if row_count else 0.0,
            approx_distinct_count=MAX_TRACKED_DISTINCT_VALUES + 1 if self.distinct_overflow else len(self.counts),
            sensitive=sensitive,
            semantic_type=semantic_type,
            top_values=top_values,
            masked_patterns=masked_patterns,
            **self.range_stats(base_type),
        )

    def infer_data_type(self, semantic_type: str | None) -> DataType:
        if semantic_type == "email":
            return DataType.EMAIL
        if semantic_type == "phone":
            return DataType.PHONE
        profile_hint = infer_profile_data_type({"name": self.name, "data_type": "string", "semantic_type": semantic_type})
        if profile_hint != DataType.STRING:
            return profile_hint
        if self.non_null_count == 0:
            return DataType.STRING
        if self.all_int:
            return DataType.INTEGER
        if self.all_float:
            return DataType.FLOAT
        if self.all_bool:
            return DataType.BOOLEAN
        if self.all_datetime:
            return DataType.DATETIME
        if self.all_date:
            return DataType.DATE
        return DataType.STRING

    def range_stats(self, data_type: DataType) -> dict[str, Any]:
        if data_type == DataType.INTEGER:
            return numeric_stats(sorted(self.integer_values), integer=True)
        if data_type == DataType.FLOAT:
            return numeric_stats(sorted(self.float_values), integer=False)
        if data_type == DataType.DATE:
            parsed = sorted(self.date_values)
            return {"min_date": parsed[0].isoformat(), "max_date": parsed[-1].isoformat()} if parsed else {}
        if data_type == DataType.DATETIME:
            parsed = sorted(self.datetime_values)
            return {"min_timestamp": parsed[0].isoformat(), "max_timestamp": parsed[-1].isoformat()} if parsed else {}
        return {}


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
