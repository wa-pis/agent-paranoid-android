import pytest

from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import Relationship, RelationshipType
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation import validate_dataset


def test_formula_solver_reports_unappliable_constraints_in_valid_mode() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[
                    FieldSpec(name="amount", data_type=FieldType.FLOAT),
                    FieldSpec(name="quantity", data_type=FieldType.FLOAT),
                ],
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.FORMULA,
                entity="orders",
                fields=["amount"],
                expression="quantity / 0",
                confidence=1.0,
            )
        ],
    )

    with pytest.raises(ValueError, match="orders.amount formula failed"):
        generate_dataset(spec, seed=3)


def test_formula_solver_leaves_unappliable_constraints_for_negative_validation() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[
                    FieldSpec(name="amount", data_type=FieldType.FLOAT),
                    FieldSpec(name="quantity", data_type=FieldType.FLOAT),
                ],
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.FORMULA,
                entity="orders",
                fields=["amount"],
                expression="quantity / 0",
                confidence=1.0,
            )
        ],
    )
    spec.generation_settings.mode = GenerationMode.NEGATIVE

    rows = generate_dataset(spec, seed=3)
    report = validate_dataset(rows, spec)

    assert rows["orders"][0]["amount"] == "not-a-number"
    assert report.valid is False


def test_aggregate_solver_does_not_crash_on_controlled_invalid_child_values() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="customers",
                row_count=1,
                fields=[
                    FieldSpec(name="customer_id", data_type=FieldType.INTEGER, is_identifier=True),
                    FieldSpec(name="total_amount", data_type=FieldType.FLOAT),
                ],
            ),
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[
                    FieldSpec(name="customer_id", data_type=FieldType.INTEGER),
                    FieldSpec(name="amount", data_type=FieldType.FLOAT),
                ],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity="customers",
                parent_field="customer_id",
                child_entity="orders",
                child_field="customer_id",
                confidence=1.0,
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.AGGREGATE_MAPPING,
                entity="customers",
                fields=["total_amount"],
                target_entity="orders",
                target_field="amount",
                confidence=1.0,
            )
        ],
    )
    spec.generation_settings.mode = GenerationMode.NEGATIVE

    rows = generate_dataset(spec, seed=3)
    report = validate_dataset(rows, spec)

    assert rows["orders"][0]["amount"] == "not-a-number"
    assert report.valid is False


def test_one_to_one_relationship_rejects_too_many_children() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="parents",
                row_count=1,
                primary_key="id",
                fields=[FieldSpec(name="id", data_type=FieldType.INTEGER, is_identifier=True)],
            ),
            EntitySpec(
                name="children",
                row_count=2,
                fields=[FieldSpec(name="parent_id", data_type=FieldType.INTEGER)],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity="parents",
                parent_field="id",
                child_entity="children",
                child_field="parent_id",
                relationship_type=RelationshipType.ONE_TO_ONE,
                confidence=1.0,
            )
        ],
    )

    with pytest.raises(ValueError, match="one_to_one"):
        generate_dataset(spec, seed=1)


def test_conditional_required_uses_field_type_default() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="orders",
                row_count=1,
                fields=[
                    FieldSpec(
                        name="status",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [{"value": "paid", "count": 1}],
                        },
                    ),
                    FieldSpec(name="amount", data_type=FieldType.INTEGER, nullable=True, null_ratio=1.0),
                ],
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.CONDITIONAL_REQUIRED,
                entity="orders",
                fields=["amount"],
                condition={"field": "status", "equals": "paid"},
                confidence=1.0,
            )
        ],
    )

    rows = generate_dataset(spec, seed=1)
    assert rows["orders"][0]["amount"] == 0


def test_aggregate_count_mapping_counts_child_rows() -> None:
    spec = DatasetSpec(
        entities=[
            EntitySpec(
                name="customers",
                row_count=1,
                primary_key="id",
                fields=[
                    FieldSpec(name="id", data_type=FieldType.INTEGER, is_identifier=True),
                    FieldSpec(name="order_count", data_type=FieldType.INTEGER),
                ],
            ),
            EntitySpec(
                name="orders",
                row_count=2,
                fields=[FieldSpec(name="customer_id", data_type=FieldType.INTEGER)],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity="customers",
                parent_field="id",
                child_entity="orders",
                child_field="customer_id",
                confidence=1.0,
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.AGGREGATE_MAPPING,
                entity="customers",
                fields=["order_count"],
                target_entity="orders",
                aggregate="count",
                confidence=1.0,
            )
        ],
    )

    rows = generate_dataset(spec, seed=1)
    assert rows["customers"][0]["order_count"] == 2
