"""Deterministic synthetic row generation."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from faker import Faker

from test_data_agent.spec import ColumnSpec, DataType, GenerationSpec, GenerationStrategy


def generate_rows(spec: GenerationSpec) -> list[dict[str, Any]]:
    rng = random.Random(spec.seed)
    faker = Faker()
    faker.seed_instance(spec.seed)

    return [
        {
            column.name: generate_value(column, row_index, rng, faker)
            for column in spec.table.columns
        }
        for row_index in range(spec.table.row_count)
    ]


def generate_value(
    column: ColumnSpec,
    row_index: int,
    rng: random.Random,
    faker: Faker,
) -> Any:
    if column.nullable and rng.random() < column.null_probability:
        return None
    if column.invalid_ratio and rng.random() < column.invalid_ratio:
        return invalid_value_for_type(column.data_type)

    strategy = column.strategy
    if strategy == GenerationStrategy.SEQUENCE:
        return row_index + 1
    if strategy == GenerationStrategy.RANDOM_INT:
        return rng.randint(int(column.min_value or 0), int(column.max_value or 9999))
    if strategy == GenerationStrategy.RANDOM_FLOAT:
        min_value = float(column.min_value if column.min_value is not None else 0.0)
        max_value = float(column.max_value if column.max_value is not None else 9999.0)
        return round(rng.uniform(min_value, max_value), 6)
    if strategy == GenerationStrategy.RANDOM_BOOLEAN:
        return rng.choice([True, False])
    if strategy == GenerationStrategy.CHOICE:
        return rng.choice(column.choices or [])
    if strategy == GenerationStrategy.CONSTANT:
        return column.constant
    if strategy == GenerationStrategy.DATE_RANGE:
        return generate_date_range_value(column, rng)
    if strategy == GenerationStrategy.DATETIME_RANGE:
        return generate_datetime_range_value(column, rng)
    if strategy == GenerationStrategy.UUID:
        return str(UUID(int=rng.getrandbits(128)))
    if strategy == GenerationStrategy.FAKER:
        return generate_faker_value(column, faker)
    raise ValueError(f"Unsupported strategy: {strategy}")


def generate_faker_value(column: ColumnSpec, faker: Faker) -> Any:
    provider_name = column.faker_provider or "word"
    provider = getattr(faker, provider_name, None)
    if provider is None:
        raise ValueError(f"Unsupported Faker provider: {provider_name}")

    value = provider()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if column.data_type == DataType.STRING:
        return str(value)
    return value


def generate_date_range_value(column: ColumnSpec, rng: random.Random) -> str:
    min_date = column.min_date or date(2000, 1, 1)
    max_date = column.max_date or date(2030, 12, 31)
    days = max(0, (max_date - min_date).days)
    return (min_date + timedelta(days=rng.randint(0, days))).isoformat()


def generate_datetime_range_value(column: ColumnSpec, rng: random.Random) -> str:
    min_datetime = column.min_datetime or datetime(2000, 1, 1)
    max_datetime = column.max_datetime or datetime(2030, 12, 31, 23, 59, 59)
    seconds = max(0, int((max_datetime - min_datetime).total_seconds()))
    return (min_datetime + timedelta(seconds=rng.randint(0, seconds))).isoformat()


def invalid_value_for_type(data_type: DataType) -> Any:
    if data_type in {DataType.INTEGER, DataType.FLOAT}:
        return "not-a-number"
    if data_type == DataType.BOOLEAN:
        return "not-a-boolean"
    if data_type in {DataType.DATE, DataType.DATETIME}:
        return "not-a-timestamp"
    return 12345
