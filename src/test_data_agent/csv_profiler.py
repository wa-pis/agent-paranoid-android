"""Safe CSV profiling for synthetic data generation.

The profiler only emits schema, aggregates, distributions, and masked patterns.
It never includes raw values for likely PII columns.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_FILE_BYTES,
    GenerationBudget,
    InputLimitError,
    configure_csv_field_limit,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
    max_input_cell_chars,
)
from test_data_agent.core.privacy import (
    LocalCategoryField,
    infer_sensitive_from_name,
    infer_sensitive_value_type,
    mask_pattern,
    semantic_type_is_sensitive,
    synthetic_category_distribution,
    validate_local_category_values,
)
from test_data_agent.profile_types import ProfileDataType, infer_profile_data_type


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
SSN_RE = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")
MAX_ENUM_VALUES = 20
MAX_TRACKED_DISTINCT_VALUES = 1_000
MAX_DISTINCT_DIGESTS = 100_000
MAX_NUMERIC_SAMPLE_VALUES = 10_000
CSV_SAMPLE_BYTES = 8192


def _csv_sensitive_value_type(value: str) -> str | None:
    if len(value) > max_input_cell_chars():
        raise InputLimitError("CSV cell exceeds character limit")
    detected = infer_sensitive_value_type(value)
    if detected not in {None, "phone"}:
        return detected
    try:
        number = Decimal(value)
    except InvalidOperation:
        return detected
    if not number.is_finite():
        return detected
    # Statistics retain binary floats. Inspect that representation as well as
    # the exact decimal; rounding must not turn an unclassified value into PII.
    # Bound magnitude before conversion or expansion of exponent notation.
    if not -64 <= number.adjusted() <= 18:
        return detected
    retained = Decimal(str(float(number)))
    # Only negative fractional measures are unambiguous here. Positive dotted
    # numbers and integral decimal identifiers remain potentially sensitive.
    if (
        detected == "phone" and re.fullmatch(r"-\d+\.\d+", value)
        and number != number.to_integral_value()
        and retained != retained.to_integral_value()
    ):
        return None
    for candidate in (number, retained):
        exponent = candidate.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -64:
            continue
        canonical = format(candidate.copy_abs(), "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
        normalized_type = infer_sensitive_value_type(canonical)
        if normalized_type == "secret":
            return normalized_type
        detected = detected or normalized_type
    return detected


@dataclass(frozen=True, slots=True)
class CSVSourceRowDigests:
    field_names: tuple[str, ...]
    digests: frozenset[bytes]


class CSVColumnProfile(BaseModel):
    name: str
    data_type: str
    decimal_precision: int | None = Field(default=None, exclude_if=lambda value: value is None)
    decimal_scale: int | None = Field(default=None, exclude_if=lambda value: value is None)
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
    local_category_fields: list[LocalCategoryField] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_local_category_fields(self) -> CSVProfile:
        available = {column.name for column in self.columns}
        references = [(item.entity, item.field) for item in self.local_category_fields]
        if len(references) != len(set(references)):
            raise ValueError("local category allowlist has duplicate fields")
        for entity, field in references:
            if entity != self.table or field not in available:
                raise ValueError(
                    f"local category allowlist references unknown field: {entity!r}.{field!r}"
                )
        return self


def profile_csv(
    path: Path,
    table_name: str | None = None,
    *,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> CSVProfile:
    return _profile_csv(
        path,
        table_name=table_name,
        local_category_fields=local_category_fields,
    )


def profile_csv_bytes(
    payload: bytes, table_name: str, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
) -> CSVProfile:
    """Profile a fixed, bounded CSV snapshot without reopening its source path."""
    budget.check("CSV snapshot profiling")
    if (type(payload) is not bytes or type(table_name) is not str or not table_name
            or type(max_bytes) is not int or max_bytes < 1 or len(payload) > max_bytes):
        raise ValueError("invalid CSV snapshot")
    return _profile_csv_rows(_csv_reader_from_snapshot(payload), table_name, (), None, budget)


def _csv_reader_from_snapshot(payload: bytes) -> csv.DictReader[str]:
    """Use identical decoding and dialect for profiling and local review."""
    configure_csv_field_limit(csv)
    encoding = "utf-8-sig"
    try:
        payload[:CSV_SAMPLE_BYTES].decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
    text = payload.decode(encoding)
    dialect = detect_csv_dialect(payload[:CSV_SAMPLE_BYTES].decode(encoding, errors="replace"))
    return csv.DictReader(io.StringIO(text, newline=""), dialect=dialect)


def profile_csv_with_row_digests(
    path: Path,
    table_name: str | None = None,
    *,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> tuple[CSVProfile, CSVSourceRowDigests]:
    digests: set[bytes] = set()
    profile = _profile_csv(
        path,
        table_name=table_name,
        row_digests=digests,
        local_category_fields=local_category_fields,
    )
    return profile, CSVSourceRowDigests(
        field_names=tuple(column.name for column in profile.columns),
        digests=frozenset(digests),
    )


def _profile_csv(
    path: Path,
    *,
    table_name: str | None = None,
    row_digests: set[bytes] | None = None,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> CSVProfile:
    enforce_input_files([path])
    configure_csv_field_limit(csv)
    encoding = detect_csv_encoding(path)
    sample = read_csv_sample(path, encoding)
    dialect = detect_csv_dialect(sample)
    with path.open(newline="", encoding=encoding) as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        return _profile_csv_rows(reader, table_name or path.stem, local_category_fields, row_digests, None)


def _profile_csv_rows(
    reader: csv.DictReader[str], table_name: str,
    local_category_fields: Sequence[LocalCategoryField], row_digests: set[bytes] | None,
    budget: GenerationBudget | None,
) -> CSVProfile:
    fieldnames = validate_csv_headers(reader.fieldnames)
    enforce_input_column_count(len(fieldnames), label="CSV")
    reader.fieldnames = fieldnames
    accumulators = {name: CSVColumnAccumulator(name) for name in fieldnames}
    row_count = 0
    for row in reader:
        if budget is not None:
            budget.check("CSV snapshot profiling")
        row_count += 1
        enforce_input_row_count(row_count, label="CSV")
        enforce_input_cell_count(row_count * len(fieldnames), label="CSV")
        for name in fieldnames:
            if budget is not None:
                budget.check("CSV snapshot profiling")
            accumulators[name].add(row.get(name, ""))
        if row_digests is not None:
            row_digests.add(csv_row_digest(row, fieldnames))
    allowed = {item.field for item in local_category_fields if item.entity == table_name}
    columns = []
    for name, accumulator in accumulators.items():
        if budget is not None:
            budget.check("CSV snapshot profiling")
        columns.append(accumulator.to_profile(row_count, preserve_categories=name in allowed))
    if budget is not None:
        budget.check("CSV snapshot profiling")
    return CSVProfile(
        table=table_name,
        row_count=row_count,
        columns=columns,
        local_category_fields=list(local_category_fields),
    )


def csv_row_digest(row: Mapping[str, Any], field_names: Sequence[str]) -> bytes:
    values = ["" if row.get(name) is None else str(row.get(name)) for name in field_names]
    payload = json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).digest()


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


def detect_csv_dialect(text: str) -> type[csv.Dialect]:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def validate_csv_headers(fieldnames: Sequence[str] | None) -> list[str]:
    if not fieldnames:
        raise ValueError("CSV must include a header row")
    normalized = [str(name).strip() for name in fieldnames]
    if any(not name for name in normalized):
        raise ValueError("CSV headers must be non-empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError("CSV headers must be unique")
    return normalized


class CSVColumnAccumulator:
    def __init__(self, name: str) -> None:
        self.name = name
        self.non_null_count = 0
        self.semantic_sample: list[str] = []
        self.content_sensitive_type: str | None = None
        self.counts: Counter[str] = Counter()
        self.distinct_overflow = False
        self.distinct_digests: set[bytes] = set()
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
        detected_type = _csv_sensitive_value_type(value)
        if detected_type == "secret" or self.content_sensitive_type is None:
            self.content_sensitive_type = detected_type
        self.add_count(value)
        self.add_typed_samples(value)

    def add_count(self, value: str) -> None:
        if len(self.distinct_digests) < MAX_DISTINCT_DIGESTS:
            self.distinct_digests.add(hashlib.sha256(value.encode()).digest())
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

    def to_profile(self, row_count: int, *, preserve_categories: bool = False) -> CSVColumnProfile:
        null_count = row_count - self.non_null_count
        semantic_type = infer_semantic_type(self.name, self.semantic_sample)
        if self.content_sensitive_type == "secret" or semantic_type is None:
            semantic_type = self.content_sensitive_type or semantic_type
        base_type = self.infer_data_type(semantic_type)
        sensitive = (
            infer_sensitive_from_name(self.name)
            or semantic_type_is_sensitive(semantic_type)
            or self.content_sensitive_type is not None
        )
        top_values: list[dict[str, Any]] = []
        masked_patterns: list[dict[str, Any]] = []
        if sensitive:
            pattern_counts: Counter[str] = Counter()
            for value, count in self.counts.items():
                value_type = _csv_sensitive_value_type(value) or semantic_type
                pattern_counts[mask_pattern(value, value_type)] += count
            masked_patterns = [{"pattern": pattern, "count": count} for pattern, count in pattern_counts.most_common(10)]
        elif (
            base_type == ProfileDataType.STRING
            and not self.distinct_overflow
            and 0 < len(self.counts) <= MAX_ENUM_VALUES
        ):
            top_values = synthetic_category_distribution(
                count for _, count in self.counts.most_common(MAX_ENUM_VALUES)
            )
        if preserve_categories:
            validate_local_category_values(
                field_name=self.name, semantic_type=semantic_type, sensitive=sensitive,
                values=self.counts, max_categories=MAX_ENUM_VALUES,
            )
            if self.distinct_overflow or base_type != ProfileDataType.STRING:
                raise ValueError("local CSV categories require a bounded string enum")
            top_values = [{"value": value, "count": count} for value, count in self.counts.most_common()]
        return CSVColumnProfile(
            name=self.name,
            data_type=base_type.value,
            nullable=null_count > 0,
            null_count=null_count,
            null_ratio=round(null_count / row_count, 6) if row_count else 0.0,
            # A capped lower bound must never certify uniqueness at the cap.
            approx_distinct_count=min(len(self.distinct_digests), MAX_DISTINCT_DIGESTS - 1),
            sensitive=sensitive,
            semantic_type=semantic_type,
            top_values=top_values,
            masked_patterns=masked_patterns,
            **({} if sensitive else self.range_stats(base_type)),
        )

    def infer_data_type(self, semantic_type: str | None) -> ProfileDataType:
        if semantic_type == "email":
            return ProfileDataType.EMAIL
        if semantic_type == "phone":
            return ProfileDataType.PHONE
        profile_hint = infer_profile_data_type({"name": self.name, "data_type": "string", "semantic_type": semantic_type})
        if profile_hint != ProfileDataType.STRING:
            return profile_hint
        if self.non_null_count == 0:
            return ProfileDataType.STRING
        if self.all_int:
            return ProfileDataType.INTEGER
        if self.all_float:
            return ProfileDataType.FLOAT
        if self.all_bool:
            return ProfileDataType.BOOLEAN
        if self.all_datetime:
            return ProfileDataType.DATETIME
        if self.all_date:
            return ProfileDataType.DATE
        return ProfileDataType.STRING

    def range_stats(self, data_type: ProfileDataType) -> dict[str, Any]:
        if data_type == ProfileDataType.INTEGER:
            return numeric_stats(sorted(self.integer_values), integer=True)
        if data_type == ProfileDataType.FLOAT:
            return numeric_stats(sorted(self.float_values), integer=False)
        if data_type == ProfileDataType.DATE:
            parsed = sorted(self.date_values)
            return {"min_date": parsed[0].isoformat(), "max_date": parsed[-1].isoformat()} if parsed else {}
        if data_type == ProfileDataType.DATETIME:
            parsed = sorted(self.datetime_values)
            return {"min_timestamp": parsed[0].isoformat(), "max_timestamp": parsed[-1].isoformat()} if parsed else {}
        return {}


def profile_column(name: str, values: list[str], row_count: int) -> CSVColumnProfile:
    non_null = [value.strip() for value in values if value is not None and value.strip() != ""]
    null_count = row_count - len(non_null)
    semantic_type = infer_semantic_type(name, non_null)
    content_sensitive_type = None
    for value in non_null:
        detected = _csv_sensitive_value_type(value)
        if detected == "secret" or content_sensitive_type is None:
            content_sensitive_type = detected
    if content_sensitive_type == "secret" or semantic_type is None:
        semantic_type = content_sensitive_type or semantic_type
    base_type = infer_data_type(name, non_null, semantic_type)
    sensitive = (
        infer_sensitive_from_name(name)
        or semantic_type_is_sensitive(semantic_type)
        or content_sensitive_type is not None
    )
    counts = Counter(non_null)

    top_values: list[dict[str, Any]] = []
    masked_patterns: list[dict[str, Any]] = []
    if sensitive:
        masked_patterns = [
            {"pattern": pattern, "count": count}
            for pattern, count in Counter(
                mask_pattern(value, _csv_sensitive_value_type(value) or semantic_type)
                for value in non_null
            ).most_common(10)
        ]
    elif base_type == ProfileDataType.STRING and 0 < len(counts) <= MAX_ENUM_VALUES:
        top_values = synthetic_category_distribution(
            count for _, count in counts.most_common(MAX_ENUM_VALUES)
        )

    stats = {} if sensitive else range_stats(non_null, base_type)
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
    if sample and sum(
        _csv_sensitive_value_type(value) == "phone" for value in sample
    ) / len(sample) >= 0.8:
        return "phone"
    return None


def infer_data_type(name: str, values: list[str], semantic_type: str | None) -> ProfileDataType:
    if semantic_type == "email":
        return ProfileDataType.EMAIL
    if semantic_type == "phone":
        return ProfileDataType.PHONE
    profile_hint = infer_profile_data_type({"name": name, "data_type": "string", "semantic_type": semantic_type})
    if profile_hint != ProfileDataType.STRING:
        return profile_hint
    if not values:
        return ProfileDataType.STRING
    if all(parse_int(value) is not None for value in values):
        return ProfileDataType.INTEGER
    if all(parse_float(value) is not None for value in values):
        return ProfileDataType.FLOAT
    if all(parse_bool(value) is not None for value in values):
        return ProfileDataType.BOOLEAN
    if all(parse_datetime_value(value) is not None for value in values):
        return ProfileDataType.DATETIME
    if all(parse_date_value(value) is not None for value in values):
        return ProfileDataType.DATE
    return ProfileDataType.STRING


def range_stats(values: list[str], data_type: ProfileDataType) -> dict[str, Any]:
    if not values:
        return {}
    if data_type == ProfileDataType.INTEGER:
        integers = sorted(int_value for value in values if (int_value := parse_int(value)) is not None)
        return numeric_stats(integers, integer=True)
    if data_type == ProfileDataType.FLOAT:
        floats = sorted(float_value for value in values if (float_value := parse_float(value)) is not None)
        return numeric_stats(floats, integer=False)
    if data_type == ProfileDataType.DATE:
        dates = sorted(item for value in values if (item := parse_date_value(value)) is not None)
        return {"min_date": dates[0].isoformat(), "max_date": dates[-1].isoformat()} if dates else {}
    if data_type == ProfileDataType.DATETIME:
        datetimes = sorted(item for value in values if (item := parse_datetime_value(value)) is not None)
        return (
            {"min_timestamp": datetimes[0].isoformat(), "max_timestamp": datetimes[-1].isoformat()}
            if datetimes
            else {}
        )
    return {}


def numeric_stats(numbers: Sequence[int | float], integer: bool) -> dict[str, Any]:
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


def percentile(numbers: Sequence[int | float], ratio: float) -> float:
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
        normalized = re.sub(r"\s+([+-]\d{2}:?\d{2})$", r"\1", value)
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
