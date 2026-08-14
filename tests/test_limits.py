from pathlib import Path
from types import SimpleNamespace

import pytest

from test_data_agent.core.limits import (
    GenerationBudget,
    GenerationLimitError,
    InputLimitError,
    enforce_output_capacity,
    enforce_output_folder_size,
)
from test_data_agent.core.serialization import load_limited_json


def test_generation_budget_rejects_expired_work() -> None:
    ticks = iter([10.0, 10.5, 11.1])
    budget = GenerationBudget(max_seconds=1.0, clock=lambda: next(ticks))

    budget.check("first stage")
    with pytest.raises(GenerationLimitError, match="during second stage"):
        budget.check("second stage")


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
def test_generation_budget_env_must_be_finite_and_positive(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_GENERATION_SECONDS", value)

    with pytest.raises(ValueError, match="finite positive"):
        GenerationBudget()


def test_output_capacity_reserves_bundle_and_free_space_floor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "100")
    monkeypatch.setenv("TEST_DATA_AGENT_MIN_FREE_DISK_BYTES", "50")
    monkeypatch.setattr(
        "test_data_agent.core.limits.shutil.disk_usage",
        lambda path: SimpleNamespace(free=149),
    )

    with pytest.raises(GenerationLimitError, match="at least 150 free bytes"):
        enforce_output_capacity(tmp_path)


def test_output_folder_limit_counts_complete_bundle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "5")
    (tmp_path / "first.txt").write_text("abc")
    (tmp_path / "second.txt").write_text("def")

    with pytest.raises(GenerationLimitError, match="bundle must be <= 5 bytes"):
        enforce_output_folder_size(tmp_path)


def test_output_folder_limit_rejects_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("safe")
    (tmp_path / "link.txt").symlink_to(target)

    with pytest.raises(GenerationLimitError, match="symbolic links"):
        enforce_output_folder_size(tmp_path)


def test_limited_json_rejects_depth_before_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_JSON_DEPTH", "1")

    def fail_if_called(payload: str) -> object:
        raise AssertionError("json.loads must not receive oversized nesting")

    monkeypatch.setattr("test_data_agent.core.serialization.json.loads", fail_if_called)

    with pytest.raises(InputLimitError, match="profile must have depth <= 1"):
        load_limited_json('{"nested": {"value": 1}}', label="profile")


def test_limited_json_ignores_structural_tokens_inside_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_JSON_DEPTH", "1")

    assert load_limited_json('{"value": "[{\\\"nested\\\": true}]"}') == {
        "value": '[{"nested": true}]'
    }
