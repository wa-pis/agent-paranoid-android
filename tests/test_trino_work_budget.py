from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from test_data_agent.trino_work_budget import (
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
    QueryWorkLimits,
    QueryWorkSnapshot,
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
