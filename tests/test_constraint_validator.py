from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.validation import validate_dataset


def test_formula_constraint_reports_evaluation_errors_without_crashing() -> None:
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

    report = validate_dataset({"orders": [{"amount": 10.0, "quantity": 2.0}]}, spec)

    assert report.valid is False
    assert "formula evaluation failed" in report.sections[2].errors[0]


def test_aggregate_mapping_reports_non_numeric_child_values_without_crashing() -> None:
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
                    FieldSpec(name="amount", data_type=FieldType.STRING),
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

    report = validate_dataset(
        {
            "customers": [{"customer_id": 1, "total_amount": 10.0}],
            "orders": [{"customer_id": 1, "amount": "not-a-number"}],
        },
        spec,
    )

    assert report.valid is False
    assert "aggregate value is not numeric" in report.sections[2].errors[0]
