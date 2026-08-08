from pathlib import Path
from typing import Any

import pytest

from test_data_agent.profiling import (
    LocalProfileBudget,
    LocalProfileDimension,
    LocalProfileLimitError,
    LocalProfileLimits,
    profile_example_folder,
)


def write_source(path: Path) -> None:
    (path / "customers.csv").write_text(
        "customer_id,status\n1,active\n2,paused\n",
        encoding="utf-8",
    )


def assert_no_cache(cache_dir: Path) -> None:
    assert not cache_dir.exists() or not list(cache_dir.glob("*.json"))


def test_local_profile_rejects_sample_request_before_cache_publication(
    tmp_path: Path,
) -> None:
    write_source(tmp_path)
    cache_dir = tmp_path / "cache"
    budget = LocalProfileBudget(LocalProfileLimits(max_sample_rows=1))

    with pytest.raises(LocalProfileLimitError) as error:
        profile_example_folder(
            tmp_path,
            cache_dir=cache_dir,
            rule_sample_rows=2,
            budget=budget,
        )

    assert error.value.dimension is LocalProfileDimension.SAMPLE_ROWS
    assert error.value.attempted == 2
    assert error.value.limit == 1
    assert_no_cache(cache_dir)


def test_local_profile_rejects_cumulative_sample_exhaustion(tmp_path: Path) -> None:
    (tmp_path / "customers.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "orders.csv").write_text("id\n2\n", encoding="utf-8")
    cache_dir = tmp_path / "cache"
    budget = LocalProfileBudget(LocalProfileLimits(max_sample_rows=1))

    with pytest.raises(LocalProfileLimitError) as error:
        profile_example_folder(
            tmp_path,
            cache_dir=cache_dir,
            rule_sample_rows=1,
            budget=budget,
        )

    assert error.value.dimension is LocalProfileDimension.SAMPLE_ROWS
    assert error.value.attempted == 2
    assert_no_cache(cache_dir)


def test_local_profile_deadline_leaves_no_partial_cache(tmp_path: Path) -> None:
    write_source(tmp_path)
    cache_dir = tmp_path / "cache"
    ticks = iter([0.0, 0.0, 0.0, 2.0])
    budget = LocalProfileBudget(
        LocalProfileLimits(max_seconds=1.0),
        clock=lambda: next(ticks, 2.0),
    )

    with pytest.raises(LocalProfileLimitError) as error:
        profile_example_folder(tmp_path, cache_dir=cache_dir, budget=budget)

    assert error.value.dimension is LocalProfileDimension.DEADLINE_SECONDS
    assert_no_cache(cache_dir)


def test_local_profile_rejects_input_bytes_before_streaming(tmp_path: Path) -> None:
    write_source(tmp_path)
    cache_dir = tmp_path / "cache"
    budget = LocalProfileBudget(LocalProfileLimits(max_input_bytes=1))

    with pytest.raises(LocalProfileLimitError) as error:
        profile_example_folder(tmp_path, cache_dir=cache_dir, budget=budget)

    assert error.value.dimension is LocalProfileDimension.INPUT_BYTES
    assert_no_cache(cache_dir)


def test_local_profile_cell_budget_leaves_no_partial_cache(tmp_path: Path) -> None:
    write_source(tmp_path)
    cache_dir = tmp_path / "cache"
    budget = LocalProfileBudget(LocalProfileLimits(max_input_cells=2))

    with pytest.raises(LocalProfileLimitError) as error:
        profile_example_folder(tmp_path, cache_dir=cache_dir, budget=budget)

    assert error.value.dimension is LocalProfileDimension.INPUT_CELLS
    assert error.value.attempted == 4
    assert_no_cache(cache_dir)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_seconds", float("inf")),
        ("max_sample_rows", 0),
        ("max_input_bytes", 0),
        ("max_input_cells", 0),
    ],
)
def test_local_profile_limits_require_positive_finite_values(
    field: str,
    value: int | float,
) -> None:
    values: dict[str, Any] = {
        "max_seconds": 1.0,
        "max_sample_rows": 1,
        "max_input_bytes": 1,
        "max_input_cells": 1,
    }
    values[field] = value

    with pytest.raises(ValueError, match="must be"):
        LocalProfileLimits(**values)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SECONDS", "0"),
        ("TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SAMPLE_ROWS", "0"),
    ],
)
def test_local_profile_environment_limits_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="positive"):
        LocalProfileBudget()
