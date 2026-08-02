from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from threading import Barrier

import pytest

from test_data_agent.trino_work_budget import (
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
    QueryWorkLimits,
    QueryWorkSnapshot,
    canonical_argument_size,
    current_query_work_budget,
    with_query_work_budget,
)


def work_limits(**overrides: int) -> QueryWorkLimits:
    values = {
        "raw_transport_payload_bytes": 100,
        "canonical_argument_bytes": 90,
        "sql_formula_chars": 80,
        "ast_nodes": 70,
        "ast_depth": 6,
        "projected_columns": 5,
        "statements": 4,
        "response_bytes": 60,
    }
    values.update(overrides)
    return QueryWorkLimits(**values)


def test_budget_tracks_every_dimension_monotonically() -> None:
    budget = QueryWorkBudget(work_limits())

    budget.consume_raw_transport_payload_bytes(10)
    budget.consume_canonical_argument_bytes(20)
    budget.consume_sql_formula_chars(30)
    budget.consume_ast_nodes(40)
    budget.observe_ast_depth(3)
    budget.observe_ast_depth(2)
    budget.consume_projected_columns(2)
    budget.consume_statements()
    budget.consume_response_bytes(50)

    assert budget.snapshot() == QueryWorkSnapshot(
        raw_transport_payload_bytes=10,
        canonical_argument_bytes=20,
        sql_formula_chars=30,
        ast_nodes=40,
        ast_depth=3,
        projected_columns=2,
        statements=1,
        response_bytes=50,
    )


def test_budget_rejects_overspend_without_restoring_prior_work() -> None:
    budget = QueryWorkBudget(work_limits(response_bytes=10))
    budget.consume_statements()
    budget.consume_response_bytes(6)

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        budget.consume_response_bytes(5)

    assert error.value.dimension is QueryWorkDimension.RESPONSE_BYTES
    assert error.value.attempted == 11
    assert error.value.limit == 10
    assert budget.snapshot().statements == 1
    assert budget.snapshot().response_bytes == 6


def test_budget_rejects_excessive_depth_without_lowering_high_water_mark() -> None:
    budget = QueryWorkBudget(work_limits(ast_depth=4))
    budget.observe_ast_depth(3)

    with pytest.raises(QueryWorkBudgetExceeded, match="AST depth"):
        budget.observe_ast_depth(5)

    assert budget.snapshot().ast_depth == 3


@pytest.mark.parametrize(
    "field",
    [
        "raw_transport_payload_bytes",
        "canonical_argument_bytes",
        "sql_formula_chars",
        "ast_nodes",
        "ast_depth",
        "projected_columns",
        "statements",
        "response_bytes",
    ],
)
def test_limits_require_positive_values(field: str) -> None:
    with pytest.raises(ValueError, match=f"{field} must be positive"):
        work_limits(**{field: 0})


def test_limits_and_snapshots_are_immutable() -> None:
    budget = QueryWorkBudget(work_limits())
    snapshot = budget.snapshot()

    with pytest.raises(FrozenInstanceError):
        budget.limits.statements = 10  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snapshot.statements = 10  # type: ignore[misc]


def test_budget_rejects_negative_consumption() -> None:
    budget = QueryWorkBudget(work_limits())

    with pytest.raises(ValueError, match="statements must be non-negative"):
        budget.consume_statements(-1)


def test_invocation_wrapper_creates_fresh_budgets_and_clears_context() -> None:
    seen: list[QueryWorkBudget] = []

    def inspect_budget(value: str = "default") -> int:
        budget = current_query_work_budget()
        assert budget is not None
        seen.append(budget)
        return budget.snapshot().canonical_argument_bytes

    wrapped = with_query_work_budget(inspect_budget, work_limits())
    expected_size = canonical_argument_size(inspect_budget)

    assert wrapped() == expected_size
    assert wrapped() == expected_size
    assert seen[0] is not seen[1]
    assert current_query_work_budget() is None


def test_invocation_wrapper_isolates_concurrent_budgets() -> None:
    barrier = Barrier(2)

    def inspect_budget(value: str) -> QueryWorkBudget:
        budget = current_query_work_budget()
        assert budget is not None
        barrier.wait(timeout=2)
        return budget

    wrapped = with_query_work_budget(inspect_budget, work_limits())
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(wrapped, value) for value in ("one", "two")]
        budgets = [future.result() for future in futures]

    assert budgets[0] is not budgets[1]
    assert current_query_work_budget() is None


def test_canonical_argument_limit_counts_utf8_and_fails_before_tool() -> None:
    calls: list[str] = []

    def record(value: str) -> None:
        calls.append(value)

    argument_size = canonical_argument_size(record, "unicodé")
    wrapped = with_query_work_budget(
        record,
        work_limits(canonical_argument_bytes=argument_size - 1),
    )

    with pytest.raises(
        QueryWorkBudgetExceeded,
        match=f"attempted {argument_size}, limit {argument_size - 1}",
    ):
        wrapped("unicodé")

    assert calls == []
    assert current_query_work_budget() is None
