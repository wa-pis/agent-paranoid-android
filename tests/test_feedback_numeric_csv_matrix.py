"""Fictional evidence for numeric CSV decisions; no privacy override is applied."""

import pytest

from test_data_agent.csv_profiler import CSVColumnAccumulator, profile_column
from test_data_agent.profiling.schema_profiler import FieldAccumulator


@pytest.mark.parametrize("route", ["column", "single_csv", "folder"])
@pytest.mark.parametrize(("values", "sensitive", "semantic"), [
    (["2468.125", "3579.625"], True, "phone"),
    (["2468125", "3579625"], True, "phone"),
    (["2.468125e3", "3.579625e3"], True, "phone"),
    (["-2468.125", "-3579.625"], False, None),
    (["-2.5"] * 105 + ["+1 (555) 010-0117"], True, "phone"),
    (["-2.5"] * 105 + ["000-12-3456"], True, "ssn"),
    (["-2.5"] * 105 + ["api_key=fictional_not_a_real_credential"], True, "secret"),
    (["-2.5"] * 105 + ["4111111111111111"], True, "secret"),
])
def test_numeric_csv_privacy_matrix(route, values, sensitive, semantic):
    if route == "column":
        profile = profile_column("quantity", values, len(values))
    else:
        accumulator = (
            CSVColumnAccumulator("quantity") if route == "single_csv"
            else FieldAccumulator("quantity")
        )
        for value in values:
            accumulator.add(value)
        profile = accumulator.to_profile(len(values))

    assert profile.sensitive is sensitive
    assert profile.semantic_type == semantic
    if sensitive:
        serialized = profile.model_dump_json()
        assert all(value not in serialized for value in set(values))
        if route == "folder":
            assert profile.distribution["kind"] == "masked_patterns"
        else:
            assert profile.top_values == []
            assert profile.min_value is None and profile.max_value is None


@pytest.mark.parametrize("route", ["column", "single_csv", "folder"])
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "1e1000000000", "not-a-number"])
def test_nonfinite_and_mixed_csv_values_do_not_become_numeric_statistics(route, value):
    values = ["-2.5", value]
    if route == "column":
        profile = profile_column("quantity", values, len(values))
    else:
        accumulator = (
            CSVColumnAccumulator("quantity") if route == "single_csv"
            else FieldAccumulator("quantity")
        )
        for item in values:
            accumulator.add(item)
        profile = accumulator.to_profile(len(values))
    assert profile.data_type == "string"
    if route == "folder":
        assert profile.distribution["kind"] != "numeric"
    else:
        assert profile.min_value is None and profile.max_value is None
