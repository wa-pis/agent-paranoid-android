"""Deterministic synthetic entity generation."""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.distribution import (
    BooleanDistribution,
    CategoricalDistribution,
    DateRangeDistribution,
    DateTimeRangeDistribution,
    NumericDistribution,
    StringPatternDistribution,
    parse_distribution,
)
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.constraint_solver import solve_constraints


def generate_dataset(spec: DatasetSpec, seed: int) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    faker = Faker()
    faker.seed_instance(seed)
    mode = spec.generation_settings.mode
    invalid_ratio = spec.generation_settings.invalid_ratio
    for entity_index, entity in enumerate(spec.entities):
        rng = random.Random(seed + entity_index)
        rows_by_entity[entity.name] = [
            generate_row(entity, row_index, rng, faker, seed, mode=mode, invalid_ratio=invalid_ratio)
            for row_index in range(entity.row_count)
        ]
    solve_constraints(rows_by_entity, spec, seed=seed)
    return rows_by_entity


def generate_row(
    entity: EntitySpec,
    row_index: int,
    rng: random.Random,
    faker: Faker,
    seed: int,
    *,
    mode: GenerationMode,
    invalid_ratio: float,
) -> dict[str, Any]:
    return {
        field.name: generate_field_value(
            entity.name,
            field,
            row_index,
            rng,
            faker,
            seed,
            mode=mode,
            invalid_ratio=invalid_ratio,
        )
        for field in entity.fields
    }


def generate_field_value(
    entity_name: str,
    field: FieldSpec,
    row_index: int,
    rng: random.Random,
    faker: Faker,
    seed: int,
    *,
    mode: GenerationMode,
    invalid_ratio: float,
) -> Any:
    if field.nullable and not field.is_identifier and rng.random() < field.null_ratio:
        return None
    if should_generate_invalid_value(field, rng, mode=mode, invalid_ratio=invalid_ratio):
        return invalid_value_for_type(field.data_type)
    if field.is_identifier:
        return synthetic_identifier(entity_name, field, row_index, seed)
    if field.sensitive:
        return synthetic_sensitive_value(field, faker)
    distribution = field.distribution or {}
    typed_distribution = parse_distribution(distribution)
    if isinstance(typed_distribution, CategoricalDistribution) and typed_distribution.categories:
        return weighted_choice(typed_distribution.categories, rng)
    numeric_distribution = typed_distribution if isinstance(typed_distribution, NumericDistribution) else None
    boolean_distribution = typed_distribution if isinstance(typed_distribution, BooleanDistribution) else None
    date_distribution = typed_distribution if isinstance(typed_distribution, DateRangeDistribution) else None
    datetime_distribution = typed_distribution if isinstance(typed_distribution, DateTimeRangeDistribution) else None
    string_distribution = typed_distribution if isinstance(typed_distribution, StringPatternDistribution) else None
    if field.data_type == FieldType.INTEGER:
        return int(round(ranged_number(numeric_distribution, distribution, rng, default_min=0, default_max=1000)))
    if field.data_type == FieldType.FLOAT:
        return round(ranged_number(numeric_distribution, distribution, rng, default_min=0.0, default_max=1000.0), 6)
    if field.data_type == FieldType.BOOLEAN:
        return boolean_value(boolean_distribution, distribution, rng)
    if field.data_type == FieldType.DATE:
        return ranged_datetime(date_distribution, distribution, rng, date_only=True)
    if field.data_type == FieldType.DATETIME:
        return ranged_datetime(datetime_distribution, distribution, rng, date_only=False)
    return synthetic_string(field, string_distribution, rng)


def synthetic_identifier(entity_name: str, field: FieldSpec, row_index: int, seed: int) -> Any:
    if field.data_type == FieldType.INTEGER:
        return seed * 1_000_000 + row_index + 1
    return f"syn_{entity_name}_{row_index + 1:08d}"


def synthetic_sensitive_value(field: FieldSpec, faker: Faker) -> str:
    if field.semantic_type == "email":
        return faker.email()
    if field.semantic_type == "phone":
        return faker.phone_number()
    if field.semantic_type == "ssn":
        return faker.ssn()
    return faker.word()


def weighted_choice(categories: list[Any], rng: random.Random) -> Any:
    def category_count(item: Any) -> float:
        if hasattr(item, "count"):
            return float(item.count)
        return float(item.get("count", 1))

    def category_value(item: Any) -> Any:
        if hasattr(item, "value"):
            return item.value
        return item.get("value")

    total = sum(category_count(item) for item in categories)
    pick = rng.uniform(0, total)
    cursor = 0.0
    for item in categories:
        cursor += category_count(item)
        if pick <= cursor:
            return category_value(item)
    return category_value(categories[-1])


def ranged_number(
    typed_distribution: NumericDistribution | None,
    distribution: dict[str, Any],
    rng: random.Random,
    default_min: float,
    default_max: float,
) -> float:
    if typed_distribution is not None:
        low = typed_distribution.p05 if typed_distribution.p05 is not None else typed_distribution.min_value
        high = typed_distribution.p95 if typed_distribution.p95 is not None else typed_distribution.max_value
    else:
        low = distribution.get("p05", distribution.get("min_value", default_min))
        high = distribution.get("p95", distribution.get("max_value", default_max))
    low = default_min if low is None else low
    high = default_max if high is None else high
    if low == high:
        return float(low)
    return rng.uniform(float(low), float(high))


def boolean_value(
    typed_distribution: BooleanDistribution | None,
    distribution: dict[str, Any],
    rng: random.Random,
) -> bool:
    true_ratio = typed_distribution.true_ratio if typed_distribution is not None else float(distribution.get("true_ratio", 0.5))
    return rng.random() < float(true_ratio)


def ranged_datetime(
    typed_distribution: DateRangeDistribution | DateTimeRangeDistribution | None,
    distribution: dict[str, Any],
    rng: random.Random,
    date_only: bool,
) -> str:
    if typed_distribution is not None:
        low = parse_datetime(typed_distribution.min) or datetime(2020, 1, 1)
        high = parse_datetime(typed_distribution.max) or datetime(2025, 1, 1)
    else:
        low = parse_datetime(distribution.get("min")) or datetime(2020, 1, 1)
        high = parse_datetime(distribution.get("max")) or datetime(2025, 1, 1)
    seconds = max(0, int((high - low).total_seconds()))
    value = low + timedelta(seconds=rng.randint(0, seconds))
    return value.date().isoformat() if date_only else value.isoformat()


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        text = str(value)
        if "T" not in text and " " not in text:
            return datetime.fromisoformat(text + "T00:00:00")
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def synthetic_string(field: FieldSpec, typed_distribution: StringPatternDistribution | None, rng: random.Random) -> str:
    distribution = field.distribution or {}
    if typed_distribution is not None:
        min_length = typed_distribution.min_length
        max_length = typed_distribution.max_length
    else:
        min_length = int(distribution.get("min_length", 6))
        max_length = int(distribution.get("max_length", max(min_length, 12)))
    length = rng.randint(max(1, min_length), max(1, max_length))
    return "syn_" + "".join(rng.choice(string.ascii_lowercase) for _ in range(length))


def should_generate_invalid_value(
    field: FieldSpec,
    rng: random.Random,
    *,
    mode: GenerationMode,
    invalid_ratio: float,
) -> bool:
    if field.is_identifier:
        return False
    if mode == GenerationMode.NEGATIVE:
        return True
    if mode != GenerationMode.MIXED:
        return False
    return invalid_ratio > 0.0 and rng.random() < invalid_ratio


def invalid_value_for_type(data_type: FieldType) -> Any:
    if data_type in {FieldType.INTEGER, FieldType.FLOAT}:
        return "not-a-number"
    if data_type == FieldType.BOOLEAN:
        return "not-a-boolean"
    if data_type in {FieldType.DATE, FieldType.DATETIME}:
        return "not-a-timestamp"
    return 12345
