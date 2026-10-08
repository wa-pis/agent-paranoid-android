"""Synthetic alias amplification is rejected before object construction."""

import pytest

from test_data_agent.core.limits import GenerationBudget, InputLimitError
from test_data_agent.core.serialization import load_limited_yaml
from test_data_agent.core.transformation_policy import BehaviorPolicyError
from test_data_agent.core.transformation_yaml import load_generation_policy_yaml


def doubling_yaml(depth: int, leaf: str = "synthetic") -> str:
    text = f"a0: &a0 {leaf}\n"
    for index in range(1, depth + 1):
        text += f"a{index}: &a{index} [*a{index - 1}, *a{index - 1}]\n"
    return text


def test_bounded_shared_alias_preserves_identity() -> None:
    result = load_limited_yaml("a: &a {value: synthetic}\nb: *a\n")
    assert result["a"] is result["b"]


@pytest.mark.parametrize("payload", ["a: &a [*a]\n", "a: &a {next: *a}\n"])
def test_recursive_alias_rejected(payload: str) -> None:
    with pytest.raises(InputLimitError, match="recursive YAML"):
        load_limited_yaml(payload)


def test_expanded_nodes_bounded_under_alias_occurrence_limit(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "1000")
    with pytest.raises(InputLimitError, match="logical expansion"):
        load_limited_yaml(doubling_yaml(12))


def test_expanded_scalar_bytes_bounded(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES", "1000")
    with pytest.raises(InputLimitError, match="logical expansion"):
        load_limited_yaml(doubling_yaml(8, "synthetic" * 8))


def test_private_policy_redacts_expansion_error(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "1000")
    with pytest.raises(BehaviorPolicyError, match="^invalid private generation policy$"):
        load_generation_policy_yaml(doubling_yaml(12).encode(), max_bytes=4096, budget=GenerationBudget())
