"""The profiling port keeps released scoped capture and request budgets."""

import csv
import io

import pytest

import test_data_agent.csv_profiler as csv_profiler
from test_data_agent.csv_profiler import _profile_csv_rows
from test_data_agent.profiling import budget as profile_budget


def test_native_distinct_deadline_uses_remaining_captured_request(monkeypatch):
    class RequestBudget:
        def check_invocation_deadline(self):
            pass

        def remaining_invocation_seconds(self):
            return 0.25

    monkeypatch.setattr(profile_budget, "current_query_work_budget", lambda: RequestBudget())
    budget = profile_budget.LocalProfileBudget(
        profile_budget.LocalProfileLimits(max_seconds=10), clock=lambda: 0,
    )
    assert budget.remaining_seconds() == 0.25


@pytest.mark.parametrize("spill", [False, True])
def test_scoped_csv_capture_keeps_empty_text_and_inspects_null_sentinel(monkeypatch, spill):
    import test_data_agent.core.privacy as privacy

    monkeypatch.setattr(privacy, "max_input_cell_chars", lambda: 5)
    if spill:
        monkeypatch.setattr(csv_profiler, "MAX_IN_MEMORY_DISTINCT", 1)
    null = "token=fictional_capture_value"
    reader = csv.DictReader(io.StringIO(f"status\n{null}\n\"\"\nordinary_value\n"))
    shapes = []
    result = _profile_csv_rows(
        reader, "records", (), None, None,
        literal_empty=True, null_token=null, max_chars=100,
        check_shape=lambda rows, columns: shapes.append((rows, columns)),
    )

    field = result.columns[0]
    assert shapes == [(0, 1), (1, 1), (2, 1), (3, 1)]
    assert result.row_count == 3
    assert field.null_count == 1
    assert field.approx_distinct_count == 2
    assert field.unique_ratio_kind == "exact"
    assert field.sensitive
    assert field.semantic_type is None
    assert null not in result.model_dump_json()


def test_sensitive_null_sentinel_cannot_supply_phone_only_numeric_replacement_evidence():
    null = "token=fictional_capture_value"
    reader = csv.DictReader(io.StringIO(f"quantity\n{null}\n2468.125\n3579.625\n"))
    profile = _profile_csv_rows(
        reader, "records", (), None, None, literal_empty=True, null_token=null,
    )
    field = profile.columns[0]
    assert field.sensitive
    assert field.semantic_type is None
    assert field.numeric_storage_type is None
    assert null not in profile.model_dump_json()
