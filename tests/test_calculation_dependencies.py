"""Formula and aggregate ordering on fictional datasets."""

from itertools import permutations
from pathlib import Path

import pytest

from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation import generate_dataset
from test_data_agent.generation.constraint_solver import solve_constraints
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.validation import validate_dataset


def calculated_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "parents", "row_count": 2, "primary_key": "id", "fields": [
                {"name": "id", "data_type": "integer", "is_identifier": True},
                {"name": "subtotal", "data_type": "integer"},
                {"name": "total", "data_type": "integer"}]},
            {"name": "children", "row_count": 4, "fields": [
                {"name": name, "data_type": "integer"}
                for name in ("parent_id", "units", "amount")]},
        ],
        "relationships": [{"parent_entity": "parents", "parent_field": "id",
                           "child_entity": "children", "child_field": "parent_id", "confidence": 1}],
        "constraints": [
            {"type": "formula", "entity": "parents", "fields": ["total"],
             "expression": "subtotal * 2", "confidence": 1},
            {"type": "aggregate_mapping", "entity": "parents", "fields": ["subtotal"],
             "target_entity": "children", "target_field": "amount", "aggregate": "sum", "confidence": 1},
            {"type": "formula", "entity": "children", "fields": ["amount"],
             "expression": "units * 2", "confidence": 1},
        ],
    })


def test_formula_aggregate_chains_ignore_declaration_order() -> None:
    spec = calculated_spec()
    expected = generate_dataset(spec, seed=1)
    for constraints in permutations(spec.constraints):
        candidate = spec.model_copy(deep=True)
        candidate.constraints = list(constraints)
        rows = generate_dataset(candidate, seed=1)
        assert rows == expected
        assert validate_dataset(rows, candidate).valid
    for parent in expected["parents"]:
        subtotal = sum(row["amount"] for row in expected["children"] if row["parent_id"] == parent["id"])
        assert parent["subtotal"] == subtotal
        assert parent["total"] == subtotal * 2


def test_multilevel_aggregate_consumes_calculated_parent_values() -> None:
    spec = calculated_spec()
    spec.entities.append(EntitySpec(name="groups", row_count=1, primary_key="id", fields=[
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="total", data_type="integer"),
    ]))
    spec.entity("parents").fields.append(FieldSpec(name="group_id", data_type="integer"))
    spec.relationships.insert(0, Relationship(parent_entity="groups", parent_field="id",
                                            child_entity="parents", child_field="group_id", confidence=1))
    spec.constraints.insert(0, Constraint(type="aggregate_mapping", entity="groups", fields=["total"],
                                         target_entity="parents", target_field="total", aggregate="sum", confidence=1))
    rows = generate_dataset(spec, seed=2)
    assert rows["groups"][0]["total"] == sum(row["total"] for row in rows["parents"])
    assert validate_dataset(rows, spec).valid


@pytest.mark.parametrize("conflict", ["cycle", "duplicate", "duplicate_aggregate"])
def test_calculation_conflicts_do_not_publish(tmp_path: Path, conflict: str) -> None:
    spec = calculated_spec()
    if conflict == "cycle":
        spec.constraints.append(Constraint(type="formula", entity="parents", fields=["id"],
                                           expression="subtotal + 1", confidence=1))
    elif conflict == "duplicate":
        spec.constraints[0].fields = ["subtotal"]
    else:
        spec.constraints.append(spec.constraints[1].model_copy(deep=True))
    with pytest.raises(ValueError, match="cyclic formula|duplicate calculated"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "output", seed=1)
    assert not (tmp_path / "output").exists()


def test_rejected_aggregate_does_not_participate_in_dependencies() -> None:
    spec = calculated_spec()
    spec.constraints[1].status = "rejected"
    rows = generate_dataset(spec, seed=1)
    assert validate_dataset(rows, spec).valid


def test_solver_preserves_large_integer_sum() -> None:
    spec = calculated_spec()
    spec.constraints = [spec.constraints[1]]
    rows = {"parents": [{"id": 1, "subtotal": 0}],
            "children": [{"parent_id": 1, "amount": 2**53}, {"parent_id": 1, "amount": 1}]}
    solve_constraints(rows, spec, seed=1)
    assert rows["parents"][0]["subtotal"] == 2**53 + 1
    assert type(rows["parents"][0]["subtotal"]) is int


def test_aggregate_keeps_conditional_default_repairs() -> None:
    spec = calculated_spec()
    spec.entity("children").field("amount").distribution = {
        "kind": "numeric", "min_value": 7, "max_value": 7,
    }
    spec.constraints = [spec.constraints[1], Constraint(type="conditional_required", entity="children",
        fields=["amount"], condition={"field": "units", "equals": 1}, confidence=1)]
    rows = {"parents": [{"id": 1, "subtotal": 0}],
            "children": [{"parent_id": 1, "units": 1, "amount": None}]}
    solve_constraints(rows, spec, seed=1)
    assert rows["children"][0]["amount"] == 7
    assert rows["parents"][0]["subtotal"] == 7


def test_deferred_formula_still_drives_conditional_required() -> None:
    spec = calculated_spec()
    for entity in spec.entities:
        entity.row_count = 1
    spec.entity("parents").fields.append(FieldSpec(name="note", data_type="string", nullable=True))
    spec.constraints.append(Constraint(type="conditional_required", entity="parents", fields=["note"],
                                      condition={"field": "total", "equals": 28}, confidence=1))
    rows = {"parents": [{"id": 1, "subtotal": 0, "total": 0, "note": None}],
            "children": [{"parent_id": 1, "units": 7, "amount": 0}]}
    solve_constraints(rows, spec, seed=1)
    assert rows["parents"][0]["total"] == 28
    assert rows["parents"][0]["note"] == "required"
    assert validate_dataset(rows, spec).valid


def test_conditional_default_feeds_next_level_aggregate() -> None:
    spec = calculated_spec()
    for entity in spec.entities:
        entity.row_count = 1
    spec.entity("parents").fields.append(FieldSpec(name="amount", data_type="integer", nullable=True,
        distribution={"kind": "numeric", "min_value": 7, "max_value": 7}))
    spec.entities.append(EntitySpec(name="groups", row_count=1, primary_key="id", fields=[
        FieldSpec(name="id", data_type="integer", is_identifier=True),
        FieldSpec(name="total", data_type="integer"),
    ]))
    spec.entity("parents").fields.append(FieldSpec(name="group_id", data_type="integer"))
    spec.relationships.insert(0, Relationship(parent_entity="groups", parent_field="id",
                                            child_entity="parents", child_field="group_id", confidence=1))
    spec.constraints.append(Constraint(type="conditional_required", entity="parents", fields=["amount"],
                                      condition={"field": "total", "equals": 28}, confidence=1))
    spec.constraints.insert(0, Constraint(type="aggregate_mapping", entity="groups", fields=["total"],
                                         target_entity="parents", target_field="amount", aggregate="sum", confidence=1))
    rows = {"groups": [{"id": 2, "total": 0}],
            "parents": [{"id": 1, "group_id": 2, "subtotal": 0, "total": 0, "amount": None}],
            "children": [{"parent_id": 1, "units": 7, "amount": 0}]}
    solve_constraints(rows, spec, seed=1)
    assert rows["parents"][0]["amount"] == rows["groups"][0]["total"] == 7
    assert validate_dataset(rows, spec).valid


def test_cyclic_temporal_repairs_fail_before_publication(tmp_path: Path) -> None:
    spec = DatasetSpec.model_validate({
        "entities": [{"name": "events", "row_count": 1, "fields": [
            {"name": name, "data_type": "date"} for name in ("start", "end")]}],
        "constraints": [{"type": "temporal", "entity": "events", "fields": fields, "confidence": 1}
                        for fields in (["start", "end"], ["end", "start"])],
    })
    with pytest.raises(ValueError, match="cyclic formula/aggregate/repair"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "output", seed=1)
    assert not (tmp_path / "output").exists()
