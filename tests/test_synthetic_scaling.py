import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.safety import SpecSafetyError, assert_spec_safe
from test_data_agent.validation import validate_dataset


def numeric_spec(*, sensitive: bool, scale_factor: float) -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name="measurements",
                row_count=20,
                fields=[
                    FieldSpec(
                        name="synthetic_total",
                        data_type=FieldType.FLOAT,
                        sensitive=sensitive,
                        distribution={
                            "kind": "numeric",
                            "p05": 1_000,
                            "p95": 2_000,
                            "scale_factor": scale_factor,
                        },
                    )
                ],
            )
        ]
    )


def test_sensitive_numeric_scaling_preserves_relative_shape_and_type() -> None:
    baseline = generate_dataset(
        numeric_spec(sensitive=False, scale_factor=1.0),
        seed=31,
    )
    scaled_spec = numeric_spec(sensitive=True, scale_factor=0.5)
    scaled = generate_dataset(scaled_spec, seed=31)

    baseline_values = [row["synthetic_total"] for row in baseline["measurements"]]
    scaled_values = [row["synthetic_total"] for row in scaled["measurements"]]

    assert scaled_values == pytest.approx([value * 0.5 for value in baseline_values])
    assert all(500 <= value <= 1_000 for value in scaled_values)
    assert validate_dataset(scaled, scaled_spec).valid is True


def test_sensitive_numeric_distribution_rejects_identity_scaling() -> None:
    spec = numeric_spec(sensitive=True, scale_factor=1.0)

    with pytest.raises(SpecSafetyError, match="non-identity numeric scale_factor"):
        assert_spec_safe(spec)
