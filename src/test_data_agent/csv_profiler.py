"""Safe CSV profiling for synthetic data generation.

The profiler only emits schema, aggregates, distributions, and masked patterns.
It never includes raw values for likely PII columns.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from fractions import Fraction
import re
from collections import Counter
from contextlib import contextmanager
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, model_validator, model_serializer
from test_data_agent.core.csv_reader import ScopedDictReader

from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_FILE_BYTES,
    DEFAULT_MAX_IN_MEMORY_DISTINCT,
    GenerationBudget,
    enforce_input_cell_count,
    enforce_input_column_count,
    enforce_input_files,
    enforce_input_row_count,
    max_input_cell_chars,
    max_local_profile_seconds,
)
from test_data_agent.core.privacy import (
    LocalCategoryField,
    SensitiveValueSignal,
    infer_sensitive_from_name,
    infer_profile_string_signal,
    mask_pattern,
    semantic_type_is_sensitive,
    synthetic_category_distribution,
    validate_local_category_values,
)
from test_data_agent.core.semantics import (
    ColumnSemanticEvidence,
    semantic_name_hint,
    supported_signal_type,
)
from test_data_agent.profile_types import ProfileDataType

from test_data_agent.trino_work_budget import generation_budget_for_invocation


if TYPE_CHECKING:
    from test_data_agent.io.csv_source import CsvSourceBinding


MAX_ENUM_VALUES = 20
MAX_TRACKED_DISTINCT_VALUES = 1_000
MAX_IN_MEMORY_DISTINCT = DEFAULT_MAX_IN_MEMORY_DISTINCT
MAX_NUMERIC_SAMPLE_VALUES = 10_000
CSV_SAMPLE_BYTES = 8192
_csv_sensitive_signal = infer_profile_string_signal


def _csv_sensitive_value_type(value: str, *, max_chars: int | None = None) -> str | None:
    signal = _csv_sensitive_signal(value, max_chars=max_chars)
    return signal.value_type if signal is not None else None


def _profile_mask_type(
    name: str, signal: SensitiveValueSignal | None, *,
    semantic_type: str | None, numeric: bool,
) -> str | None:
    if signal is None:
        return semantic_type
    return supported_signal_type(
        signal, hint=semantic_name_hint(name, numeric=numeric), numeric=numeric,
    )


def _column_semantic_evidence(
    values: Iterable[str], *, max_chars: int | None = None,
) -> ColumnSemanticEvidence:
    evidence = ColumnSemanticEvidence()
    for raw_value in values:
        value = raw_value.strip()
        if not value:
            continue
        integer = parse_int(value)
        number = parse_float(value)
        evidence.add(
            _csv_sensitive_signal(value, max_chars=max_chars),
            numeric=integer is not None or (number is not None and math.isfinite(number)),
        )
    return evidence


@dataclass(frozen=True, slots=True)
class CSVSourceRowDigests:
    field_names: tuple[str, ...]
    digests: frozenset[bytes]


class CSVColumnProfile(BaseModel):
    name: str
    data_type: str
    decimal_precision: int | None = Field(default=None)
    decimal_scale: int | None = Field(default=None)
    nullable: bool
    null_count: int | None
    null_ratio: float | None
    approx_distinct_count: int | None
    unique_ratio_kind: Literal["unspecified", "exact", "lower_bound"] = "unspecified"
    sensitive: bool
    semantic_type: str | None = None
    numeric_storage_type: Literal["integer", "float"] | None = None
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

    @model_serializer(mode="wrap")
    def serialize_optional_fields(self, handler: Any) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        for name in ("decimal_precision", "decimal_scale", "numeric_storage_type"):
            if getattr(self, name) is None:
                payload.pop(name, None)
        return payload


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
    budget: GenerationBudget | None = None,
    source_binding: CsvSourceBinding | None = None,
) -> CSVProfile:
    return _profile_csv(
        path,
        table_name=table_name,
        local_category_fields=local_category_fields,
        budget=budget,
        source_binding=source_binding,
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


def _csv_reader_from_snapshot(payload: bytes, *, max_chars: int | None = None,
                              check_size: Callable[[int], None] | None = None) -> csv.DictReader[str]:
    """Use identical decoding and dialect for profiling and local review."""
    encoding = "utf-8-sig"
    try:
        payload[:CSV_SAMPLE_BYTES].decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
    text = payload.decode(encoding)
    dialect = detect_csv_dialect(payload[:CSV_SAMPLE_BYTES].decode(encoding, errors="replace"))
    return ScopedDictReader(io.StringIO(text, newline=""), dialect=dialect,
                            max_chars=max_chars, check_size=check_size)


def profile_csv_with_row_digests(
    path: Path,
    table_name: str | None = None,
    *,
    local_category_fields: Sequence[LocalCategoryField] = (),
    budget: GenerationBudget | None = None,
) -> tuple[CSVProfile, CSVSourceRowDigests]:
    digests: set[bytes] = set()
    profile = _profile_csv(
        path,
        table_name=table_name,
        row_digests=digests,
        local_category_fields=local_category_fields,
        budget=budget,
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
    budget: GenerationBudget | None = None,
    source_binding: CsvSourceBinding | None = None,
) -> CSVProfile:
    budget = budget or generation_budget_for_invocation(max_seconds=max_local_profile_seconds())
    budget.check("CSV profiling preflight")
    enforce_input_files([path])
    if source_binding is not None:
        with bound_csv_reader(path, source_binding, check=lambda: budget.check("CSV profiling")) as reader:
            return _profile_csv_rows(reader, table_name or path.stem, local_category_fields, row_digests, budget)
    encoding = detect_csv_encoding(path)
    sample = read_csv_sample(path, encoding)
    dialect = detect_csv_dialect(sample)
    with path.open(newline="", encoding=encoding) as handle:
        reader = ScopedDictReader(handle, dialect=dialect)
        return _profile_csv_rows(reader, table_name or path.stem, local_category_fields, row_digests, budget)


def _profile_csv_rows(
    reader: csv.DictReader[str], table_name: str,
    local_category_fields: Sequence[LocalCategoryField], row_digests: set[bytes] | None,
    budget: GenerationBudget | None,
    *, literal_empty: bool = False, null_token: str | None = None,
    check_shape: Callable[[int, int], None] | None = None,
    max_chars: int | None = None,
) -> CSVProfile:
    from test_data_agent.profiling import duckdb_distinct
    from test_data_agent.profiling.budget import (
        LocalProfileBudget,
        default_local_profile_limits,
    )

    limits = default_local_profile_limits()
    if budget is not None:
        limits = replace(limits, max_seconds=min(limits.max_seconds, budget.remaining_seconds()))
    work_budget = LocalProfileBudget(limits)
    fieldnames = validate_csv_headers(reader.fieldnames)
    if check_shape is None:
        enforce_input_column_count(len(fieldnames), label="CSV")
    else:
        check_shape(0, len(fieldnames))
    reader.fieldnames = fieldnames
    accumulators = {name: CSVColumnAccumulator(name, max_chars=max_chars) for name in fieldnames}
    ordered_accumulators = list(accumulators.values())
    row_count = 0

    def cells() -> Iterator[tuple[int, bytes]]:
        nonlocal row_count
        for row in reader:
            work_budget.check_deadline("CSV row start")
            if budget is not None:
                budget.check("CSV snapshot profiling")
            row_count += 1
            if check_shape is None:
                enforce_input_row_count(row_count, label="CSV")
                enforce_input_cell_count(row_count * len(fieldnames), label="CSV")
            else:
                check_shape(row_count, len(fieldnames))
            for column, accumulator in enumerate(ordered_accumulators):
                work_budget.check_deadline("CSV field profiling")
                if budget is not None:
                    budget.check("CSV snapshot profiling")
                raw = row.get(accumulator.name, "")
                if literal_empty and raw == null_token:
                    accumulator.observe_sensitivity(raw)
                    continue
                digest = accumulator.add(raw, literal_empty=literal_empty)
                if digest is not None:
                    yield column, digest
            if row_digests is not None:
                row_digests.add(csv_row_digest(row, fieldnames))

    values = cells()
    sizes = [0] * len(fieldnames)
    tracked = 0
    for column, _ in values:
        size = len(ordered_accumulators[column].distinct_digests)
        tracked += size - sizes[column]
        sizes[column] = size
        if tracked > MAX_IN_MEMORY_DISTINCT:
            for accumulator in ordered_accumulators:
                accumulator.distinct_count = 0
            counts = duckdb_distinct.count_distinct_stream(
                [item.distinct_digests for item in ordered_accumulators], values, work_budget,
            )
            for accumulator, count in zip(ordered_accumulators, counts, strict=True):
                accumulator.distinct_count = count
            break
    allowed = {item.field for item in local_category_fields if item.entity == table_name}
    columns = []
    for name, accumulator in accumulators.items():
        work_budget.check_deadline("CSV field finalization")
        if budget is not None:
            budget.check("CSV snapshot profiling")
        columns.append(accumulator.to_profile(row_count, preserve_categories=name in allowed))
    if budget is not None:
        budget.check("CSV snapshot profiling")
    work_budget.check_deadline("CSV profile finalization")
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


@contextmanager
def bound_csv_reader(
    path: Path, binding: CsvSourceBinding, *, check: Callable[[], None],
) -> Iterator[csv.DictReader[str]]:
    with binding.read(path, check=check) as source:
        sample = source.peek(CSV_SAMPLE_BYTES)[:CSV_SAMPLE_BYTES]
        encoding = _csv_sample_encoding(sample)
        dialect = detect_csv_dialect(sample.decode(encoding, errors="replace"))
        text = io.TextIOWrapper(source, encoding=encoding, newline="")
        try:
            yield ScopedDictReader(text, dialect=dialect)
        finally:
            text.detach()


def detect_csv_encoding(path: Path) -> str:
    with path.open("rb") as handle:
        raw = handle.read(CSV_SAMPLE_BYTES)
    return _csv_sample_encoding(raw)


def _csv_sample_encoding(raw: bytes) -> str:
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
    def __init__(self, name: str, *, max_chars: int | None = None) -> None:
        self.name = name
        self.max_chars = max_input_cell_chars() if max_chars is None else max_chars
        if type(self.max_chars) is not int or self.max_chars < 1:
            raise ValueError("invalid CSV character limit")
        self.non_null_count = 0
        self.semantic_evidence = ColumnSemanticEvidence()
        self.extra_sensitive = False
        self.counts: Counter[str] = Counter()
        self.distinct_overflow = False
        self.distinct_digests: set[bytes] = set()
        self.distinct_count: int | None = None
        self.integer_values: list[int] = []
        self.float_values: list[float] = []
        self.date_values: list[date] = []
        self.datetime_values: list[datetime] = []
        self.all_int = True
        self.all_float = True
        self.all_bool = True
        self.all_datetime = True
        self.all_date = True

    def add(self, raw_value: str | None, *, literal_empty: bool = False) -> bytes | None:
        value = raw_value.strip() if raw_value is not None else ""
        if value == "" and not literal_empty:
            return None
        self.non_null_count += 1
        signal = _csv_sensitive_signal(value, max_chars=self.max_chars)
        digest = self.add_count(value)
        numeric = self.add_typed_samples(value)
        self.semantic_evidence.add(signal, numeric=numeric)
        return digest

    def observe_sensitivity(self, value: str) -> None:
        # Null sentinels still require inspection, but do not support semantics.
        signal = _csv_sensitive_signal(value.strip(), max_chars=self.max_chars)
        self.extra_sensitive = self.extra_sensitive or signal is not None

    def add_count(self, value: str) -> bytes:
        digest = hashlib.sha256(value.encode()).digest()
        if self.distinct_count is None:
            self.distinct_digests.add(digest)
        if value in self.counts:
            self.counts[value] += 1
            return digest
        if len(self.counts) < MAX_TRACKED_DISTINCT_VALUES:
            self.counts[value] = 1
            return digest
        self.distinct_overflow = True
        return digest

    def add_typed_samples(self, value: str) -> bool:
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
        return parsed_int is not None or (
            parsed_float is not None and math.isfinite(parsed_float)
        )

    def to_profile(self, row_count: int, *, preserve_categories: bool = False) -> CSVColumnProfile:
        null_count = row_count - self.non_null_count
        semantic_type = self.semantic_evidence.resolve(self.name)
        base_type = self.infer_data_type(semantic_type)
        sensitive = (
            infer_sensitive_from_name(self.name)
            or semantic_type_is_sensitive(semantic_type)
            or self.semantic_evidence.sensitive
            or self.extra_sensitive
        )
        top_values: list[dict[str, Any]] = []
        masked_patterns: list[dict[str, Any]] = []
        if sensitive:
            pattern_counts: Counter[str] = Counter()
            for value, count in self.counts.items():
                value_type = _profile_mask_type(
                    self.name, _csv_sensitive_signal(value, max_chars=self.max_chars), semantic_type=semantic_type,
                    numeric=self.semantic_evidence.all_numeric,
                )
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
            approx_distinct_count=(self.distinct_count if self.distinct_count is not None
                                   else len(self.distinct_digests)),
            unique_ratio_kind="exact",
            sensitive=sensitive,
            semantic_type=semantic_type,
            numeric_storage_type=None if self.extra_sensitive else _numeric_storage_type(
                semantic_type, self.non_null_count, self.all_int, self.all_float,
                evidence=self.semantic_evidence,
            ),
            top_values=top_values,
            masked_patterns=masked_patterns,
            **({} if sensitive else self.range_stats(base_type)),
        )

    def infer_data_type(self, semantic_type: str | None) -> ProfileDataType:
        if semantic_type in {"email", "phone", "name", "address"}:
            return ProfileDataType(semantic_type)
        if semantic_type == "ssn":
            return ProfileDataType.STRING
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
    evidence = _column_semantic_evidence(non_null)
    semantic_type = evidence.resolve(name)
    base_type = infer_data_type(name, non_null, semantic_type)
    sensitive = (
        infer_sensitive_from_name(name)
        or semantic_type_is_sensitive(semantic_type)
        or evidence.sensitive
    )
    counts = Counter(non_null)

    top_values: list[dict[str, Any]] = []
    masked_patterns: list[dict[str, Any]] = []
    if sensitive:
        masked_patterns = [
            {"pattern": pattern, "count": count}
            for pattern, count in Counter(
                mask_pattern(value, _profile_mask_type(
                    name, _csv_sensitive_signal(value), semantic_type=semantic_type,
                    numeric=evidence.all_numeric,
                ))
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
        unique_ratio_kind="exact",
        sensitive=sensitive,
        semantic_type=semantic_type,
        numeric_storage_type=_numeric_storage_type(
            semantic_type, len(non_null),
            all(parse_int(value) is not None for value in non_null),
            all(parse_float(value) is not None for value in non_null),
            evidence=evidence,
        ),
        top_values=top_values,
        masked_patterns=masked_patterns,
        **stats,
    )


def _numeric_storage_type(
    semantic_type: str | None, non_null: int, all_integer: bool, all_float: bool,
    *, evidence: ColumnSemanticEvidence | None = None,
) -> Literal["integer", "float"] | None:
    """Retain finite phone-only numeric evidence without assigning semantics."""
    if not non_null or semantic_type not in {None, "phone"}:
        return None
    if evidence is None:
        if semantic_type != "phone":
            return None
    elif set(evidence.matches) != {SensitiveValueSignal.PHONE}:
        return None
    return "integer" if all_integer else "float" if all_float else None


def infer_semantic_type(name: str, values: list[str], *, max_chars: int | None = None) -> str | None:
    return _column_semantic_evidence(values, max_chars=max_chars).resolve(name)


def infer_data_type(name: str, values: list[str], semantic_type: str | None) -> ProfileDataType:
    if semantic_type in {"email", "phone", "name", "address"}:
        return ProfileDataType(semantic_type)
    if semantic_type == "ssn":
        return ProfileDataType.STRING
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
    }
    for key, numerator in (("p05", 1), ("p95", 19)):
        if integer:
            lower, weight = divmod((len(numbers) - 1) * numerator, 20)
            upper = min(lower + 1, len(numbers) - 1)
            # Round once, before binary FLOAT can change the integer endpoints.
            interpolated = (Fraction(numbers[lower]) * (20 - weight)
                            + Fraction(numbers[upper]) * weight) / 20
            stats[key] = round(interpolated)
        else:
            stats[key] = percentile(numbers, numerator / 20)
    if integer:
        stats = {key: int(round(value)) for key, value in stats.items()}
    return stats


def percentile(numbers: Sequence[int | float], ratio: float) -> int | float:
    index = ratio * (len(numbers) - 1)
    lower = int(index)
    upper = min(lower + 1, len(numbers) - 1)
    weight = index - lower
    if weight == 0 or numbers[lower] == numbers[upper]:
        return numbers[lower]
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
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
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
