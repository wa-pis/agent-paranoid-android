"""Synthetic identifier domains must not invent undeclared relationships."""

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation import validate_dataset


@pytest.mark.parametrize("data_type", ["integer", "string"])
@pytest.mark.parametrize("seed", [-2, 0, 7])
def test_identifier_domains_are_distinct_and_declared_links_still_work(data_type, seed):
    spec = DatasetSpec(entities=[
        EntitySpec(name=name, row_count=4, fields=[
            FieldSpec(name=field, data_type=data_type, is_identifier=True)
            for field in ("id", "ref_id")
        ]) for name in ("items", "orders")
    ])
    rows = generate_dataset(spec, seed=seed)
    domains = [
        {row[field] for row in rows[name]}
        for name in ("items", "orders") for field in ("id", "ref_id")
    ]
    assert all(len(domain) == 4 for domain in domains)
    assert len(set.union(*domains)) == 16
    assert rows == generate_dataset(spec, seed=seed)
    spec.entities.reverse()
    for entity in spec.entities:
        entity.fields.reverse()
    assert rows == generate_dataset(spec, seed=seed)
    spec.relationships.append(Relationship(
        parent_entity="items", parent_field="id", child_entity="orders",
        child_field="ref_id", relationship_type="many_to_one",
        confidence=1, status="confirmed",
    ))
    linked = generate_dataset(spec, seed=seed)
    assert {row["ref_id"] for row in linked["orders"]} == domains[0]
    assert validate_dataset(linked, spec).valid
