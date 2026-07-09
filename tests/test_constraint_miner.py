from test_data_agent.core.constraint import ConstraintType
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.profiling.constraint_miner import infer_conditional_required_constraints


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
