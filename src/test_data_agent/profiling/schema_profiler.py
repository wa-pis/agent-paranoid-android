"""Schema profiling for folders of CSV files."""

from __future__ import annotations

import csv
import random
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.csv_profiler import (
    infer_data_type,
    infer_semantic_type,
    mask_pattern,
    numeric_stats,
    parse_bool,
    parse_date_value,
    parse_datetime_value,
    parse_float,
    parse_int,
)
from test_data_agent.spec import infer_sensitive_from_name

MAX_DISTINCT_TRACKED = 200_000
MAX_CATEGORY_TRACKED = 1_000
MAX_RESERVOIR_VALUES = 10_000
MAX_SEMANTIC_SAMPLE = 100


def load_csv_folder(input_folder: Path, max_rows_per_entity: int | None = None) -> dict[str, list[dict[str, str]]]:
    rows_by_entity: dict[str, list[dict[str, str]]] = {}
    for path in sorted(input_folder.glob("*.csv")):
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"CSV must include a header row: {path}")
            rows: list[dict[str, str]] = []
            for row in reader:
                rows.append(dict(row))
                if max_rows_per_entity is not None and len(rows) >= max_rows_per_entity:
                    break
            rows_by_entity[path.stem] = rows
    if not rows_by_entity:
        raise ValueError(f"no CSV files found in {input_folder}")
    return rows_by_entity


def profile_schema(input_folder: Path) -> DatasetProfile:
    entities: list[EntityProfile] = []
    csv_paths = sorted(input_folder.glob("*.csv"))
    if not csv_paths:
        raise ValueError(f"no CSV files found in {input_folder}")
    for path in csv_paths:
        entity_name = path.stem
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"CSV must include a header row: {path}")
            accumulators = {name: FieldAccumulator(name=name) for name in reader.fieldnames}
            row_count = 0
            for row in reader:
                row_count += 1
                for name, accumulator in accumulators.items():
                    accumulator.add(row.get(name, ""))
        fields = [accumulator.to_profile(row_count) for accumulator in accumulators.values()]
        primary_key_candidates = [field.name for field in fields if field.is_identifier and field.unique_ratio >= 0.98]
        entities.append(
            EntityProfile(
                name=entity_name,
                row_count=row_count,
                fields=fields,
                primary_key_candidates=primary_key_candidates,
            )
        )
    return DatasetProfile(entities=entities)


def profile_field(name: str, values: list[str], row_count: int) -> FieldProfile:
    non_null = [value.strip() for value in values if value is not None and value.strip() != ""]
    distinct_count = len(set(non_null))
    semantic_type = infer_semantic_type(name, non_null)
    data_type = infer_data_type(name, non_null, semantic_type)
    unique_ratio = distinct_count / len(non_null) if non_null else 0.0
    is_identifier = is_identifier_name(name) or (unique_ratio >= 0.98 and "id" in name.lower())
    sensitive = infer_sensitive_from_name(name) or semantic_type in {"email", "phone", "ssn"}
    return FieldProfile(
        name=name,
        data_type=normalize_field_type(data_type.value),
        nullable=len(non_null) < row_count,
        null_ratio=round((row_count - len(non_null)) / row_count, 6) if row_count else 0.0,
        unique_ratio=round(unique_ratio, 6),
        sensitive=sensitive,
        semantic_type=semantic_type,
        is_identifier=is_identifier,
    )


def is_identifier_name(name: str) -> bool:
    lowered = name.lower()
    return lowered == "id" or lowered.endswith("_id")


def normalize_field_type(value: str) -> FieldType:
    if value in {item.value for item in FieldType}:
        return FieldType(value)
    return FieldType.STRING


@dataclass
class FieldAccumulator:
    name: str
    row_count: int = 0
    null_count: int = 0
    non_null_count: int = 0
    semantic_sample: list[str] = field(default_factory=list)
    distinct_values: set[str] = field(default_factory=set)
    distinct_overflow: bool = False
    duplicate_seen: bool = False
    category_counts: Counter[str] = field(default_factory=Counter)
    category_overflow: bool = False
    numeric_values: list[int | float] = field(default_factory=list)
    date_values: list[date] = field(default_factory=list)
    datetime_values: list[datetime] = field(default_factory=list)
    bool_counts: Counter[bool] = field(default_factory=Counter)
    min_length: int | None = None
    max_length: int | None = None
    possible_int: bool = True
    possible_float: bool = True
    possible_bool: bool = True
    possible_date: bool = True
    possible_datetime: bool = True
    rng: random.Random = field(default_factory=lambda: random.Random(0))

    def add(self, raw_value: str | None) -> None:
        self.row_count += 1
        value = "" if raw_value is None else str(raw_value).strip()
        if value == "":
            self.null_count += 1
            return
        self.non_null_count += 1
        if len(self.semantic_sample) < MAX_SEMANTIC_SAMPLE:
            self.semantic_sample.append(value)
        self.track_distinct(value)
        self.track_category(value)
        self.track_types(value)
        length = len(value)
        self.min_length = length if self.min_length is None else min(self.min_length, length)
        self.max_length = length if self.max_length is None else max(self.max_length, length)

    def track_distinct(self, value: str) -> None:
        if value in self.distinct_values:
            self.duplicate_seen = True
            return
        if len(self.distinct_values) < MAX_DISTINCT_TRACKED:
            self.distinct_values.add(value)
        else:
            self.distinct_overflow = True

    def track_category(self, value: str) -> None:
        if self.category_overflow:
            return
        if value not in self.category_counts and len(self.category_counts) >= MAX_CATEGORY_TRACKED:
            self.category_overflow = True
            self.category_counts.clear()
            return
        self.category_counts[value] += 1

    def track_types(self, value: str) -> None:
        int_value = parse_int(value)
        float_value = parse_float(value)
        bool_value = parse_bool(value)
        datetime_value = parse_datetime_value(value)
        date_value = parse_date_value(value)

        self.possible_int = self.possible_int and int_value is not None
        self.possible_float = self.possible_float and float_value is not None
        self.possible_bool = self.possible_bool and bool_value is not None
        self.possible_datetime = self.possible_datetime and datetime_value is not None
        self.possible_date = self.possible_date and date_value is not None

        if int_value is not None:
            self.reservoir_add(self.numeric_values, int_value)
        elif float_value is not None:
            self.reservoir_add(self.numeric_values, float_value)
        if bool_value is not None:
            self.bool_counts[bool_value] += 1
        if datetime_value is not None:
            self.reservoir_add(self.datetime_values, datetime_value)
        elif date_value is not None:
            self.reservoir_add(self.date_values, date_value)

    def reservoir_add(self, values: list[Any], value: Any) -> None:
        if len(values) < MAX_RESERVOIR_VALUES:
            values.append(value)
            return
        index = self.rng.randint(0, self.non_null_count - 1)
        if index < MAX_RESERVOIR_VALUES:
            values[index] = value

    def to_profile(self, table_row_count: int) -> FieldProfile:
        semantic_type = infer_semantic_type(self.name, self.semantic_sample)
        data_type = self.infer_field_type(semantic_type)
        unique_ratio = self.estimate_unique_ratio()
        is_identifier = is_identifier_name(self.name) or (unique_ratio >= 0.98 and "id" in self.name.lower())
        sensitive = infer_sensitive_from_name(self.name) or semantic_type in {"email", "phone", "ssn"}
        profile = FieldProfile(
            name=self.name,
            data_type=data_type,
            nullable=self.null_count > 0,
            null_ratio=round(self.null_count / table_row_count, 6) if table_row_count else 0.0,
            unique_ratio=round(unique_ratio, 6),
            sensitive=sensitive,
            semantic_type=semantic_type,
            is_identifier=is_identifier,
        )
        profile.distribution = self.distribution(profile)
        return profile

    def infer_field_type(self, semantic_type: str | None) -> FieldType:
        if semantic_type in {"email", "phone", "ssn"}:
            return FieldType.STRING
        if self.non_null_count == 0:
            return FieldType.STRING
        if self.possible_int:
            return FieldType.INTEGER
        if self.possible_float:
            return FieldType.FLOAT
        if self.possible_bool:
            return FieldType.BOOLEAN
        if self.possible_datetime:
            return FieldType.DATETIME
        if self.possible_date:
            return FieldType.DATE
        return FieldType.STRING

    def estimate_unique_ratio(self) -> float:
        if self.non_null_count == 0:
            return 0.0
        if self.distinct_overflow and not self.duplicate_seen:
            return 1.0
        return len(self.distinct_values) / self.non_null_count

    def distribution(self, profile: FieldProfile) -> dict[str, Any]:
        if profile.is_identifier:
            return {"kind": "synthetic_identifier"}
        if profile.sensitive:
            patterns = Counter(mask_pattern(value, profile.semantic_type) for value in self.semantic_sample)
            return {"kind": "masked_patterns", "patterns": [{"pattern": pattern, "count": count} for pattern, count in patterns.most_common(10)]}
        if profile.data_type == FieldType.INTEGER:
            numbers = sorted(value for value in self.numeric_values if isinstance(value, int))
            return {"kind": "numeric", **numeric_stats(numbers, integer=True)}
        if profile.data_type == FieldType.FLOAT:
            numbers = sorted(float(value) for value in self.numeric_values)
            return {"kind": "numeric", **numeric_stats(numbers, integer=False)}
        if profile.data_type == FieldType.BOOLEAN:
            return {"kind": "boolean", "true_ratio": self.bool_counts[True] / self.non_null_count if self.non_null_count else 0.0}
        if profile.data_type == FieldType.DATE:
            values = sorted(self.date_values)
            return {"kind": "date_range", "min": values[0].isoformat(), "max": values[-1].isoformat()} if values else {"kind": "date_range"}
        if profile.data_type == FieldType.DATETIME:
            values = sorted(self.datetime_values)
            return {"kind": "datetime_range", "min": values[0].isoformat(), "max": values[-1].isoformat()} if values else {"kind": "datetime_range"}
        if not self.category_overflow and 0 < len(self.category_counts) <= 20:
            return {"kind": "categorical", "categories": [{"value": value, "count": count} for value, count in self.category_counts.most_common(20)]}
        return {"kind": "string_pattern", "min_length": self.min_length or 1, "max_length": self.max_length or 12}
