from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.profiling.constraint_miner import (
    infer_aggregate_mapping_constraints,
    infer_conditional_required_constraints,
)


def test_conditional_required_constraints_use_typed_categorical_distributions() -> None:
    fields = [
        FieldProfile(
            name="status",
            data_type=FieldType.STRING,
            distribution={
                "kind": "categorical",
                "categories": [
                    {"value": "paid", "count": 3},
                    {"value": "draft", "count": 1},
                ],
            },
        ),
        FieldProfile(name="paid_at", data_type=FieldType.DATETIME, nullable=True),
    ]
    rows = [
        {"status": "paid", "paid_at": "2024-01-01T09:00:00"},
        {"status": "paid", "paid_at": "2024-01-02T09:00:00"},
        {"status": "paid", "paid_at": "2024-01-03T09:00:00"},
        {"status": "draft", "paid_at": ""},
    ]

    constraints = infer_conditional_required_constraints("orders", rows, fields)

    assert len(constraints) == 1
    assert constraints[0].type == ConstraintType.CONDITIONAL_REQUIRED
    assert constraints[0].entity == "orders"
    assert constraints[0].fields == ["paid_at"]
    assert constraints[0].condition == {"field": "status", "equals": "paid"}
    assert constraints[0].confidence == 1.0


def test_average_mapping_is_inferred_from_reviewable_field_name() -> None:
    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="customers",
                row_count=1,
                fields=[
                    FieldProfile(
                        name="customer_id",
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="orders_amount_average",
                        data_type=FieldType.FLOAT,
                    ),
                ],
            ),
            EntityProfile(
                name="orders",
                row_count=2,
                fields=[
                    FieldProfile(
                        name="customer_id",
                        data_type=FieldType.INTEGER,
                    ),
                    FieldProfile(name="amount", data_type=FieldType.FLOAT),
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
    )

    constraints = infer_aggregate_mapping_constraints(profile)

    assert len(constraints) == 1
    assert constraints[0].fields == ["orders_amount_average"]
    assert constraints[0].target_field == "amount"
    assert constraints[0].aggregate == "avg"
