"""Boundary evidence for the existing source-free prevalence contract."""

import pytest

from test_data_agent.core.distribution import NumericShapeDistribution
from test_data_agent.profiling.numeric_shape import shape_prevalence


def test_legacy_shape_does_not_invent_prevalence_or_change_serialization():
    assert shape_prevalence({}, 7) == {}
    payload = {"kind": "numeric_shape", "max_abs_magnitude": -3,
               "has_negative": False, "has_positive": True}
    shape = NumericShapeDistribution.model_validate(payload)
    assert shape.model_dump() == payload
    assert shape.zero_ratio is None and shape.subunit_ratio is None


def test_prevalence_uses_nonnull_denominator_and_retains_subunit_order():
    metadata = shape_prevalence(
        {"zero_count": 2, "subunit_count": 3, "min_subunit_magnitude": -8}, 5,
    )
    assert metadata == {"zero_ratio": 0.4, "subunit_ratio": 0.6,
                        "min_subunit_magnitude": -8}
    assert shape_prevalence(
        {"zero_count": None, "subunit_count": None}, 0,
    ) == {}


@pytest.mark.parametrize("summary", [
    {"zero_count": True, "subunit_count": 0},
    {"zero_count": -1, "subunit_count": 0},
    {"zero_count": 1.5, "subunit_count": 0},
    {"zero_count": 3, "subunit_count": 3},
    {"zero_count": 0},
    {"zero_count": 0, "subunit_count": 1, "min_subunit_magnitude": 0},
    {"zero_count": 0, "subunit_count": 1, "min_subunit_magnitude": -309},
    {"zero_count": 0, "subunit_count": 1, "min_subunit_magnitude": -1.5},
    {"zero_count": 0, "subunit_count": 0, "min_subunit_magnitude": -1},
])
def test_malformed_prevalence_is_rejected_without_partial_numeric_evidence(summary):
    with pytest.raises(ValueError, match="numeric prevalence"):
        shape_prevalence(summary, 5)
