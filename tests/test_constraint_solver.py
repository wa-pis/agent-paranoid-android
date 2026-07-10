from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation import validate_dataset


def test_formula_solver_leaves_unappliable_constraints_for_validation() -> None:
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

    rows = generate_dataset(spec, seed=3)
    report = validate_dataset(rows, spec)

    assert rows["orders"][0]["amount"] is not None
    assert report.valid is False
    assert "formula evaluation failed" in report.sections[2].errors[0]


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
