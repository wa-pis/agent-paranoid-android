"""Versioned deterministic row tiles independent of process scheduling."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.generation.entity_generator import create_faker, generate_row


ENGINE_VERSION = "tiled-v1"
TILE_ROWS = 4096


def generate_tile(
    spec: DatasetSpec,
    entity_index: int,
    start: int,
    seed: int,
    *,
    budget: GenerationBudget,
) -> list[dict[str, Any]]:
    """Generate one fixed logical tile; callers own global solving/validation."""
    if type(entity_index) is not int or not 0 <= entity_index < len(spec.entities):
        raise ValueError("tile entity index is out of range")
    entity = spec.entities[entity_index]
    if type(start) is not int or start < 0 or start % TILE_ROWS or start >= entity.row_count:
        raise ValueError("tile start must be an aligned row index within the entity")
    budget.check("tile setup")
    payload = json.dumps(
        [ENGINE_VERSION, seed, entity.name, start // TILE_ROWS],
        ensure_ascii=True, separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    faker = create_faker(spec.generation_settings.locale)
    faker.seed_instance(int.from_bytes(digest[16:], "big"))
    distributions = [field.typed_distribution for field in entity.fields]
    identifier_domains = {
        key: index for index, key in enumerate(sorted(
            (item.name, field.name)
            for item in spec.entities for field in item.fields
            if field.is_identifier
        ))
    }
    rows: list[dict[str, Any]] = []
    for row_index in range(start, min(start + TILE_ROWS, entity.row_count)):
        budget.check("tile row generation")
        rows.append(generate_row(
            entity, row_index, rng, faker, seed,
            mode=spec.generation_settings.mode,
            invalid_ratio=spec.generation_settings.invalid_ratio,
            identifier_domains=identifier_domains,
            distributions=distributions,
        ))
    return rows
