"""Typed work limits for one local CSV-folder profile."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path

from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_CELLS,
    DEFAULT_MAX_LOCAL_PROFILE_SAMPLE_ROWS,
    DEFAULT_MAX_LOCAL_PROFILE_SECONDS,
    DEFAULT_MAX_TOTAL_INPUT_BYTES,
    InputLimitError,
    enforce_input_cell_count,
    enforce_input_files,
    max_input_cells,
    max_local_profile_sample_rows,
    max_local_profile_seconds,
    max_total_input_bytes,
)


class LocalProfileDimension(StrEnum):
    DEADLINE_SECONDS = "deadline_seconds"
    SAMPLE_ROWS = "sample_rows"
    INPUT_BYTES = "input_bytes"
    INPUT_CELLS = "input_cells"


class LocalProfileLimitError(InputLimitError):
    """Structured fail-closed limit error without source values."""

    def __init__(
        self,
        dimension: LocalProfileDimension,
        *,
        attempted: int | float,
        limit: int | float,
        stage: str,
    ) -> None:
        self.dimension = dimension
        self.attempted = attempted
        self.limit = limit
        self.stage = stage
        super().__init__(
            f"local profile {dimension.value} budget exceeded during {stage}: "
            f"attempted {attempted:g}, limit {limit:g}"
        )


@dataclass(frozen=True, slots=True)
class LocalProfileLimits:
    max_seconds: float = DEFAULT_MAX_LOCAL_PROFILE_SECONDS
    max_sample_rows: int = DEFAULT_MAX_LOCAL_PROFILE_SAMPLE_ROWS
    max_input_bytes: int = DEFAULT_MAX_TOTAL_INPUT_BYTES
    max_input_cells: int = DEFAULT_MAX_INPUT_CELLS

    def __post_init__(self) -> None:
        if not isfinite(self.max_seconds) or self.max_seconds <= 0:
            raise ValueError("local profile max_seconds must be finite and positive")
        for name in ("max_sample_rows", "max_input_bytes", "max_input_cells"):
            if getattr(self, name) < 1:
                raise ValueError(f"local profile {name} must be positive")


def default_local_profile_limits() -> LocalProfileLimits:
    return LocalProfileLimits(
        max_seconds=max_local_profile_seconds(),
        max_sample_rows=max_local_profile_sample_rows(),
        max_input_bytes=max_total_input_bytes(),
        max_input_cells=max_input_cells(),
    )


class LocalProfileBudget:
    """Monotonic budget owned by exactly one profiling invocation."""

    def __init__(
        self,
        limits: LocalProfileLimits | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limits = limits or default_local_profile_limits()
        self._clock = clock
        self._started_at = clock()
        self._sample_rows = 0
        self._input_cells = 0

    def check_deadline(self, stage: str) -> None:
        elapsed = self._clock() - self._started_at
        if elapsed >= self.limits.max_seconds:
            raise LocalProfileLimitError(
                LocalProfileDimension.DEADLINE_SECONDS,
                attempted=elapsed,
                limit=self.limits.max_seconds,
                stage=stage,
            )

    def check_sample_rows(self, requested: int) -> None:
        if requested > self.limits.max_sample_rows:
            raise LocalProfileLimitError(
                LocalProfileDimension.SAMPLE_ROWS,
                attempted=requested,
                limit=self.limits.max_sample_rows,
                stage="sample configuration",
            )

    def consume_sample_row(self) -> None:
        attempted = self._sample_rows + 1
        if attempted > self.limits.max_sample_rows:
            raise LocalProfileLimitError(
                LocalProfileDimension.SAMPLE_ROWS,
                attempted=attempted,
                limit=self.limits.max_sample_rows,
                stage="row-level sampling",
            )
        self._sample_rows = attempted

    def check_input_files(self, paths: Iterable[Path]) -> list[Path]:
        resolved = list(paths)
        total_bytes = 0
        for path in resolved:
            if path.is_symlink():
                raise InputLimitError(
                    f"symbolic link inputs are not allowed: {path.name!r}"
                )
            if not path.is_file():
                raise InputLimitError(
                    f"input path must be a regular file: {path.name!r}"
                )
            total_bytes += path.stat().st_size
        if total_bytes > self.limits.max_input_bytes:
            raise LocalProfileLimitError(
                LocalProfileDimension.INPUT_BYTES,
                attempted=total_bytes,
                limit=self.limits.max_input_bytes,
                stage="input preflight",
            )
        return enforce_input_files(resolved)

    def consume_cells(self, amount: int) -> None:
        attempted = self._input_cells + amount
        if attempted > self.limits.max_input_cells:
            raise LocalProfileLimitError(
                LocalProfileDimension.INPUT_CELLS,
                attempted=attempted,
                limit=self.limits.max_input_cells,
                stage="CSV streaming",
            )
        enforce_input_cell_count(attempted, label="CSV folder")
        self._input_cells = attempted
