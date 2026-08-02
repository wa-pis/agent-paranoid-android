from __future__ import annotations

from scripts.benchmark_trino_invocation_defaults import (
    REPRESENTATIVE_COLUMNS,
    run_invocation_default_benchmark,
)
from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS


def test_invocation_defaults_cover_representative_profile_fanout() -> None:
    metrics = run_invocation_default_benchmark()

    assert DEFAULT_QUERY_WORK_LIMITS.max_profiled_columns == 100
    assert DEFAULT_QUERY_WORK_LIMITS.statements == 150
    assert DEFAULT_QUERY_WORK_LIMITS.max_invocation_seconds == 120.0
    assert metrics.profiled_columns == REPRESENTATIVE_COLUMNS
    assert metrics.statements == 122
    assert metrics.statement_headroom == 28
    assert metrics.elapsed_seconds < metrics.configured_deadline_seconds
    assert metrics.remaining_deadline_seconds > 0
