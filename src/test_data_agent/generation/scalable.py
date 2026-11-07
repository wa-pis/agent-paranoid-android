"""Bounded row tasks for scalable-v1; no filesystem or provider access."""
from __future__ import annotations
import random
import resource
import sys
import time
from dataclasses import dataclass
from typing import Any

from test_data_agent.core.dataset import DatasetSpec, RESERVED_ENTITY_ARTIFACT_BASENAMES
from test_data_agent.core.distribution import SyntheticIdentifierDistribution
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.generation.entity_generator import create_faker, generate_row
from test_data_agent.safety import assert_spec_safe
from test_data_agent.validation.reconciliation import assert_generated_dataset_valid


@dataclass(frozen=True)
class RowTask:
    spec: DatasetSpec
    entity_index: int
    start: int
    count: int
    seed: int


@dataclass(frozen=True)
class RowBatch:
    rows: list[dict[str, Any]]
    memory_bytes: int
    generation_seconds: float
    validation_seconds: float


def resident_high_water_bytes() -> int:
    amount = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(amount if sys.platform == "darwin" else amount*1024)


def check_scalable_spec(spec: DatasetSpec) -> None:
    policy = spec.generation_settings.execution_policy
    if policy is None:
        raise ValueError("scalable generation requires an explicit execution policy")
    assert_spec_safe(spec)
    if spec.relationships or spec.constraints or spec.business_rules or spec.relational_scenarios:
        raise ValueError("scalable-v1 supports independent tables only; use the legacy engine for relationships or global rules")
    if spec.generation_settings.mode not in {"valid", "edge"}:
        raise ValueError("scalable-v1 supports valid and edge modes only")
    rows = sum(entity.row_count for entity in spec.entities)
    cells = sum(entity.row_count*len(entity.fields) for entity in spec.entities)
    if rows > policy.max_rows or cells > policy.max_cells:
        raise GenerationLimitError("large run exceeds execution-policy rows or cells; review a larger finite policy")
    names = [entity.name.casefold() for entity in spec.entities]
    if len(set(names)) != len(names):
        raise ValueError('scalable entity artifact names must be distinct ignoring case')
    for entity in spec.entities:
        if entity.name.casefold() in RESERVED_ENTITY_ARTIFACT_BASENAMES | {'generation_statistics'}:
            raise ValueError('entity name is reserved by scalable-v1')
        if policy.require_distinct_rows and (entity.primary_key is None or not entity.field(entity.primary_key).is_identifier):
            raise ValueError("distinct scalable rows require a synthetic-identifier primary key")
        if entity.primary_key is not None:
            field = entity.field(entity.primary_key)
            distribution = field.typed_distribution
            if not field.is_identifier or (isinstance(distribution, SyntheticIdentifierDistribution)
                    and distribution.pool_size is not None and distribution.pool_size < entity.row_count):
                raise ValueError("scalable primary key must have a sufficient synthetic identifier domain")
        # Reject oversized batches before allocation; Python object overhead is budgeted separately.
        max_cell = max((int(f.distribution.get("max_length", 128)) for f in entity.fields), default=0)
        if policy.batch_size*max(1, len(entity.fields))*(max_cell*4+256) > policy.max_memory_bytes//(2*(policy.workers+1)):
            raise GenerationLimitError("batch working set exceeds memory policy; review a smaller batch size")


def generate_task(task: RowTask, *, budget: GenerationBudget | None = None) -> RowBatch:
    spec = task.spec
    policy = spec.generation_settings.execution_policy
    assert policy is not None
    budget = budget or GenerationBudget(policy.max_seconds)
    budget.check('scalable task setup')
    started = time.monotonic()
    entity = spec.entities[task.entity_index]
    domains = {key: index for index, key in enumerate(sorted(
        (e.name, f.name) for e in spec.entities for f in e.fields if f.is_identifier))}
    faker = create_faker(spec.generation_settings.locale)
    seeded_faker = any(field.sensitive for field in entity.fields)
    rows = []
    for index in range(task.start, task.start+task.count):
        budget.check("scalable row generation")
        # Row-local integer streams: independent of process scheduling and batch boundaries.
        row_seed = (task.seed & ((1 << 64)-1)) ^ ((task.entity_index+1) << 96) ^ (index << 128)
        rng = random.Random(row_seed)
        if seeded_faker:
            faker.seed_instance(row_seed)
        rows.append(generate_row(entity, index, rng, faker, task.seed,
            mode=spec.generation_settings.mode, invalid_ratio=0,
            identifier_domains=domains))
    generated = time.monotonic()
    chunk = spec.model_copy(update={
        "entities": [entity.model_copy(update={"row_count": task.count})],
        "privacy_rules": [rule for rule in spec.privacy_rules if rule.entity in (None, entity.name)],
        "local_category_fields": [field for field in spec.local_category_fields if field.entity == entity.name],
    })
    assert_generated_dataset_valid({entity.name: rows}, chunk, budget=budget)
    memory = resident_high_water_bytes()
    if memory > policy.max_memory_bytes//(policy.workers+1):
        raise GenerationLimitError("worker memory exceeded execution policy; reduce workers or batch size")
    return RowBatch(rows, memory, generated-started, time.monotonic()-generated)
