"""Deterministic synthetic entity generation."""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.generation.constraint_solver import solve_constraints


def generate_dataset(spec: DatasetSpec, seed: int) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    faker = Faker()
    faker.seed_instance(seed)
    for entity_index, entity in enumerate(spec.entities):
        rng = random.Random(seed + entity_index)
        rows_by_entity[entity.name] = [generate_row(entity, row_index, rng, faker, seed) for row_index in range(entity.row_count)]
    solve_constraints(rows_by_entity, spec, seed=seed)
    return rows_by_entity


def generate_row(entity: EntitySpec, row_index: int, rng: random.Random, faker: Faker, seed: int) -> dict[str, Any]:
    return {field.name: generate_field_value(entity.name, field, row_index, rng, faker, seed) for field in entity.fields}


def generate_field_value(entity_name: str, field: FieldSpec, row_index: int, rng: random.Random, faker: Faker, seed: int) -> Any:
    if field.nullable and not field.is_identifier and rng.random() < field.null_ratio:
        return None
    if field.is_identifier:
        return synthetic_identifier(entity_name, field, row_index, seed)
    if field.sensitive:
        return synthetic_sensitive_value(field, faker)
    distribution = field.distribution or {}
    kind = distribution.get("kind")
    if kind == "categorical":
        categories = distribution.get("categories", [])
        if categories:
            return weighted_choice(categories, rng)
    if field.data_type == FieldType.INTEGER:
        return int(round(ranged_number(distribution, rng, default_min=0, default_max=1000)))
    if field.data_type == FieldType.FLOAT:
        return round(ranged_number(distribution, rng, default_min=0.0, default_max=1000.0), 6)
    if field.data_type == FieldType.BOOLEAN:
        return rng.random() < float(distribution.get("true_ratio", 0.5))
    if field.data_type == FieldType.DATE:
        return ranged_datetime(distribution, rng, date_only=True)
    if field.data_type == FieldType.DATETIME:
        return ranged_datetime(distribution, rng, date_only=False)
    return synthetic_string(field, rng)


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


def weighted_choice(categories: list[dict[str, Any]], rng: random.Random) -> Any:
    total = sum(float(item.get("count", 1)) for item in categories)
    pick = rng.uniform(0, total)
    cursor = 0.0
    for item in categories:
        cursor += float(item.get("count", 1))
        if pick <= cursor:
            return item.get("value")
    return categories[-1].get("value")


def ranged_number(distribution: dict[str, Any], rng: random.Random, default_min: float, default_max: float) -> float:
    low = distribution.get("p05", distribution.get("min_value", default_min))
    high = distribution.get("p95", distribution.get("max_value", default_max))
    if low == high:
        return float(low)
    return rng.uniform(float(low), float(high))


def ranged_datetime(distribution: dict[str, Any], rng: random.Random, date_only: bool) -> str:
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


def synthetic_string(field: FieldSpec, rng: random.Random) -> str:
    distribution = field.distribution or {}
    min_length = int(distribution.get("min_length", 6))
    max_length = int(distribution.get("max_length", max(min_length, 12)))
    length = rng.randint(max(1, min_length), max(1, max_length))
    return "syn_" + "".join(rng.choice(string.ascii_lowercase) for _ in range(length))
