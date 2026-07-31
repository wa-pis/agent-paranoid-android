from __future__ import annotations

import pytest

from scripts.check_operational_budgets import (
    OperationalBudgetError,
    PhaseMetrics,
    enforce_phase_budget,
    run_operational_budget_check,
)


def test_operational_budget_check_exercises_all_phases() -> None:
    metrics = run_operational_budget_check(row_count=100)

    assert [metric.name for metric in metrics] == ["profile", "generate", "validate"]
    assert all(metric.elapsed_seconds >= 0 for metric in metrics)
    assert all(metric.peak_bytes > 0 for metric in metrics)


@pytest.mark.parametrize(
    ("metrics", "match"),
    [
        (PhaseMetrics("generate", 2.0, 10), "2.000s exceeds 1.000s"),
        (PhaseMetrics("profile", 0.1, 11), "11 peak bytes exceeds 10"),
    ],
)
def test_operational_budget_rejects_regressions(
    metrics: PhaseMetrics, match: str
) -> None:
    with pytest.raises(OperationalBudgetError, match=match):
        enforce_phase_budget(metrics, max_seconds=1.0, max_peak_bytes=10)
