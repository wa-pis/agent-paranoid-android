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


def test_declared_fk_retains_requested_row_counts_without_orphans():
    spec = DatasetSpec(entities=[
        EntitySpec(name="parents", row_count=4, primary_key="id", fields=[
            FieldSpec(name="id", data_type="integer", is_identifier=True)
        ]),
        EntitySpec(name="children", row_count=100, fields=[
            FieldSpec(name="parent_id", data_type="integer", is_identifier=True)
        ]),
    ])
    unlinked = generate_dataset(spec, seed=17)
    parents = {row["id"] for row in unlinked["parents"]}
    assert len(unlinked["children"]) == 100
    assert parents.isdisjoint({row["parent_id"] for row in unlinked["children"]})

    spec.relationships.append(Relationship(
        parent_entity="parents", parent_field="id", child_entity="children",
        child_field="parent_id", confidence=1, status="confirmed",
    ))
    linked = generate_dataset(spec, seed=17)
    assert len(linked["parents"]) == 4
    assert len(linked["children"]) == 100
    assert {row["parent_id"] for row in linked["children"]} == parents
    assert validate_dataset(linked, spec).valid


@pytest.mark.parametrize("data_type", ["integer", "string"])
def test_reversed_foreign_key_chain_uses_final_parent_keys(data_type):
    spec = DatasetSpec(entities=[
        EntitySpec(name=name, row_count=4, primary_key="id", fields=[
            FieldSpec(name="id", data_type=data_type, is_identifier=True)
        ]) for name in ("a", "b", "c")
    ], relationships=[
        Relationship(parent_entity=parent, parent_field="id", child_entity=child,
                     child_field="id", confidence=1, status="confirmed")
        for parent, child in (("b", "c"), ("a", "b"))
    ])
    rows = generate_dataset(spec, seed=7)
    assert rows["a"] == rows["b"] == rows["c"]
    assert validate_dataset(rows, spec).valid


def test_nullable_identifier_domains_are_disjoint_where_present():
    spec = DatasetSpec(entities=[EntitySpec(name="items", row_count=10, fields=[
        FieldSpec(name=name, data_type="integer", is_identifier=True,
                  nullable=True, null_ratio=0.5)
        for name in ("left_id", "right_id")
    ])])
    rows = generate_dataset(spec, seed=7)
    assert rows == generate_dataset(spec, seed=7)
    for reverse in (False, True):
        if reverse:
            spec.entities[0].fields.reverse()
        rows = generate_dataset(spec, seed=7)["items"]
        values = [{row[name] for row in rows if row[name] is not None}
                  for name in ("left_id", "right_id")]
        assert values[0] and values[1] and values[0].isdisjoint(values[1])


def test_existing_relationship_cycle_remains_validated():
    spec = DatasetSpec(entities=[
        EntitySpec(name=name, row_count=2, fields=[
            FieldSpec(name="id", data_type="integer", is_identifier=True)
        ]) for name in ("a", "b")
    ], relationships=[
        Relationship(parent_entity=parent, parent_field="id", child_entity=child,
                     child_field="id", confidence=1, status="confirmed")
        for parent, child in (("a", "b"), ("b", "a"))
    ])
    assert validate_dataset(generate_dataset(spec, seed=7), spec).valid


def test_unrelated_cycle_does_not_disable_parent_first_chain():
    spec = DatasetSpec(entities=[
        EntitySpec(name=name, row_count=4, primary_key="id", fields=[
            FieldSpec(name="id", data_type="integer", is_identifier=True)
        ]) for name in ("a", "b", "c", "x", "y")
    ], relationships=[
        Relationship(parent_entity=parent, parent_field="id", child_entity=child,
                     child_field="id", confidence=1, status="confirmed")
        for parent, child in (("b", "c"), ("a", "b"), ("x", "y"), ("y", "x"))
    ])
    rows = generate_dataset(spec, seed=7)
    assert rows["a"] == rows["b"] == rows["c"]
    assert validate_dataset(rows, spec).valid
    spec.relationships[1].status = "rejected"
    assert validate_dataset(generate_dataset(spec, seed=7), spec).valid
