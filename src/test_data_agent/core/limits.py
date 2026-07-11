"""Shared resource limits for synthetic data generation."""

from __future__ import annotations

import os


MAX_GENERATION_COUNT_ENV = "TEST_DATA_AGENT_MAX_GENERATION_COUNT"
DEFAULT_MAX_GENERATION_COUNT = 100_000


def max_generation_count() -> int:
    raw_value = os.environ.get(MAX_GENERATION_COUNT_ENV)
    if raw_value is None:
        return DEFAULT_MAX_GENERATION_COUNT
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{MAX_GENERATION_COUNT_ENV} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{MAX_GENERATION_COUNT_ENV} must be positive")
    return value


def enforce_row_count_limit(row_count: int, *, max_count: int | None = None) -> None:
    effective_max = max_generation_count() if max_count is None else max_count
    if row_count > effective_max:
        raise ValueError(f"row_count must be <= {effective_max}")
