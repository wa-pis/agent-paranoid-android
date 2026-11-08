"""Bounded source-free dependency planning and synthetic reference proofs."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.generation.entity_generator import synthetic_identifier
from test_data_agent.validation.relationship_validator import RelationshipMetrics

RELATIONAL_ENGINE = 'scalable-relational-v1'


@dataclass(frozen=True)
class SyntheticReference:
    parent_entity: str
    parent_field: FieldSpec
    child_entity: str
    child_field: str
    parent_rows: int
    domain: int
    domain_count: int
    one_to_one: bool
    stream: int

    def value(self, ordinal: int, seed: int) -> Any:
        if not self.one_to_one:
            # A private stream never consumes the ordinary field/null-mask RNG.
            ordinal = random.Random(seed ^ (ordinal << 128) ^ ((self.stream+1) << 192)).randrange(self.parent_rows)
        return synthetic_identifier(self.parent_entity, self.parent_field, ordinal, seed,
                                    domain=self.domain, domain_count=self.domain_count)


@dataclass(frozen=True)
class RelationalPlan:
    entity_order: tuple[int, ...]
    incoming: tuple[tuple[SyntheticReference, ...], ...]
    domains: dict[tuple[str, str], int]


def plan_relational_spec(spec: DatasetSpec, *, budget: GenerationBudget) -> RelationalPlan:
    """Admit only finite DAGs whose parent key domains can be proved symbolically."""
    if len(spec.entities) > 100 or len(spec.relationships) > 1000 or sum(len(e.fields) for e in spec.entities) > 10_000:
        raise GenerationLimitError('relational graph exceeds 100 entities, 1000 relationships or 10000 fields')
    budget.consume_rule_work(len(spec.entities)+len(spec.relationships)+sum(len(e.fields) for e in spec.entities))
    entities = {entity.name: index for index, entity in enumerate(spec.entities)}
    domains = {key: index for index, key in enumerate(sorted(
        (entity.name, field.name) for entity in spec.entities for field in entity.fields if field.is_identifier))}
    incoming: list[list[SyntheticReference]] = [[] for _ in spec.entities]
    dependencies: list[set[int]] = [set() for _ in spec.entities]
    targets: set[tuple[str, str]] = set()
    fields = {(entity.name, field.name): field for entity in spec.entities for field in entity.fields}
    for stream, relationship in enumerate(spec.relationships):
        budget.check('relational graph admission')
        if relationship.status == 'rejected':
            continue
        parent_index = entities.get(relationship.parent_entity)
        child_index = entities.get(relationship.child_entity)
        parent_field = fields.get((relationship.parent_entity, relationship.parent_field))
        child_field = fields.get((relationship.child_entity, relationship.child_field))
        if parent_index is None or child_index is None or parent_field is None or child_field is None:
            raise ValueError('relational graph references unknown entities or fields')
        parent, child = spec.entities[parent_index], spec.entities[child_index]
        if parent_index == child_index:
            raise ValueError('scalable relational generation rejects self-links and cycles')
        if (parent.primary_key != parent_field.name or not parent_field.is_identifier or parent_field.nullable
                or parent_field.data_type not in {FieldType.INTEGER, FieldType.STRING}):
            raise ValueError('scalable relationships require a non-null synthetic integer/string parent primary key')
        if child.primary_key == child_field.name:
            raise ValueError('scalable relationships do not support shared primary-key/foreign-key identity')
        if child_field.data_type != parent_field.data_type:
            raise ValueError('relational parent and child key types must match')
        target = (child.name, child_field.name)
        if target in targets:
            raise ValueError('multiple active relationships target the same child field')
        targets.add(target)
        if relationship.relationship_type not in {RelationshipType.MANY_TO_ONE, RelationshipType.ONE_TO_ONE}:
            raise ValueError('unsupported scalable relationship cardinality')
        one_to_one = relationship.relationship_type == RelationshipType.ONE_TO_ONE
        if parent.row_count < 1 or (one_to_one and child.row_count > parent.row_count):
            raise ValueError('one-to-one child count requires a sufficient generated parent domain')
        dependencies[child_index].add(parent_index)
        incoming[child_index].append(SyntheticReference(parent.name, parent_field, child.name, child_field.name,
            parent.row_count, domains[parent.name, parent_field.name], max(1, len(domains)), one_to_one, stream))
    # Stable Kahn traversal retains original indices for deterministic tie-breaking.
    order: list[int] = []
    remaining = set(range(len(spec.entities)))
    while remaining:
        budget.consume_rule_work(len(remaining))
        ready = sorted(index for index in remaining if dependencies[index].isdisjoint(remaining))
        if not ready:
            raise ValueError('scalable relational generation rejects cycles; review an acyclic dependency graph')
        order.extend(ready)
        remaining.difference_update(ready)
    return RelationalPlan(tuple(order), tuple(tuple(links) for links in incoming), domains)


def assign_references(row: dict[str, Any], links: tuple[SyntheticReference, ...], ordinal: int, seed: int) -> None:
    for link in links:
        if row[link.child_field] is not None:
            row[link.child_field] = link.value(ordinal, seed)


def validate_relational_rows(spec: DatasetSpec, plan: RelationalPlan, entity_index: int,
                             rows: list[dict[str, Any]], *, start: int, seed: int,
                             budget: GenerationBudget) -> list[RelationshipMetrics]:
    """Prove actual key/reference assignments using bounded scalar state only."""
    entity = spec.entities[entity_index]
    links = plan.incoming[entity_index]
    nullable = [entity.field(link.child_field).nullable for link in links]
    counts = [[0, 0] for _ in links]  # non-null, null; no row/key sets
    budget.consume_rule_work(len(rows)*(len(links)+1))
    primary = entity.field(entity.primary_key) if entity.primary_key is not None else None
    for ordinal, row in enumerate(rows, start=start):
        budget.check('streamed relational proof')
        if primary is not None:
            expected = synthetic_identifier(entity.name, primary, ordinal, seed,
                domain=plan.domains[entity.name, primary.name], domain_count=max(1, len(plan.domains)))
            if str(row.get(primary.name)) != str(expected):
                raise ValueError('generated parent/child primary-key domain or ordering is invalid')
        for index, link in enumerate(links):
            value = row.get(link.child_field)
            if value is None:
                if not nullable[index]:
                    raise ValueError('non-nullable synthetic foreign key is missing')
                counts[index][1] += 1
            else:
                if str(value) != str(link.value(ordinal, seed)):
                    raise ValueError('synthetic foreign-key assignment does not match the reviewed parent domain')
                counts[index][0] += 1
    return [RelationshipMetrics(parent_entity=link.parent_entity, parent_field=link.parent_field.name,
        child_entity=entity.name, child_field=link.child_field, parent_distinct_keys=link.parent_rows,
        checked_references=checked, resolved_references=checked, null_references=nulls,
        resolution_ratio=1.0 if checked else None, valid=True)
        for link, (checked, nulls) in zip(links, counts, strict=True)]


def merge_relationship_metrics(total: list[RelationshipMetrics], batch: list[RelationshipMetrics]) -> None:
    for item in batch:
        existing = next((old for old in total if (old.parent_entity, old.parent_field, old.child_entity, old.child_field)
                         == (item.parent_entity, item.parent_field, item.child_entity, item.child_field)), None)
        if existing is None:
            total.append(item.model_copy(deep=True))
        else:
            existing.checked_references += item.checked_references
            existing.resolved_references += item.resolved_references
            existing.null_references += item.null_references
            existing.resolution_ratio = 1.0 if existing.checked_references else None
