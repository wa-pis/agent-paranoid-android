"""Synthetic inference stops inside combinatorial work, before publication."""

import pytest

from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling.budget import LocalProfileBudget, LocalProfileDimension, LocalProfileLimits, LocalProfileLimitError
from test_data_agent.profiling.constraint_miner import infer_formula_constraints, formula_confidence


def test_formula_candidates_charge_even_without_rows():
    budget = LocalProfileBudget(LocalProfileLimits(max_inference_evaluations=5))
    with pytest.raises(LocalProfileLimitError) as error:
        infer_formula_constraints("items", [], [f"metric_{i}" for i in range(20)], budget=budget)
    assert error.value.dimension is LocalProfileDimension.INFERENCE_EVALUATIONS
    assert error.value.attempted == 6


def test_deadline_stops_between_formula_rows():
    now = [0.0]
    budget = LocalProfileBudget(LocalProfileLimits(max_seconds=1), clock=lambda: now[0])
    calls = []
    def op(a, b):
        calls.append(1)
        now[0] = 2
        return a + b
    rows = [{"a": "1", "b": "2", "c": "3"}] * 10
    with pytest.raises(LocalProfileLimitError):
        formula_confidence(rows, "c", "a", "b", op, budget=budget)
    assert len(calls) == 1


def test_wide_folder_fails_without_cache(tmp_path):
    (tmp_path / "metrics.csv").write_text(",".join(f"metric_{i}" for i in range(8)) + "\n" +
        (",".join(["10"] * 8) + "\n") * 4)
    cache = tmp_path / "cache"
    budget = LocalProfileBudget(LocalProfileLimits(max_inference_evaluations=10))
    with pytest.raises(LocalProfileLimitError):
        profile_example_folder(tmp_path, cache_dir=cache, budget=budget)
    assert not cache.exists()


def test_inference_work_is_cumulative_across_calls():
    budget = LocalProfileBudget(LocalProfileLimits(max_inference_evaluations=8))
    fields = ["a", "b", "c"]
    assert infer_formula_constraints("first", [], fields, budget=budget) == []
    with pytest.raises(LocalProfileLimitError):
        infer_formula_constraints("second", [], fields, budget=budget)


def test_first_successful_formula_semantics_preserved():
    rows = [{"a": "6", "b": "2", "c": "3"}] * 2
    result = infer_formula_constraints("items", rows, ["a", "b", "c"])
    assert len(result) == 1 and result[0].expression == "b * c"
    assert result[0].confidence == 1


def test_inference_inherits_request_deadline(monkeypatch):
    from dataclasses import replace
    from test_data_agent.trino_work_budget import (
        DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, QueryWorkBudgetExceeded,
        with_query_work_budget,
    )
    now = [0.0]
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=1)
    request = QueryWorkBudget(limits, monotonic_clock=lambda: now[0])
    calls = []
    def op(a, b):
        calls.append(1)
        now[0] = 2
        return a + b
    def run():
        return formula_confidence([{"a": "1", "b": "2", "c": "3"}] * 4,
                                  "c", "a", "b", op)
    with pytest.raises(QueryWorkBudgetExceeded):
        with_query_work_budget(run, limits, budget_provider=lambda: request)()
    assert len(calls) == 1
