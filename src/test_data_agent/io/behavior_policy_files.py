"""Restricted local policy persistence; never an approval mechanism."""

from pathlib import Path

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, BehaviorPolicyError
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml, load_behavior_policy_yaml
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
from test_data_agent.io.path_policy import atomic_binary_writer


def load_behavior_policy_file(
    root: Path, relative_path: str, *, max_bytes: int, budget: GenerationBudget,
) -> BehaviorPolicy:
    try:
        snapshot = read_mapping_snapshot(root, relative_path, max_bytes=max_bytes, budget=budget)
        return load_behavior_policy_yaml(snapshot.payload, max_bytes=max_bytes, budget=budget)
    except (OSError, ValueError):
        pass
    try:
        raise BehaviorPolicyError("invalid private policy file")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise


def save_behavior_policy_file(
    root: Path, relative_path: str, policy: BehaviorPolicy, *, max_bytes: int, budget: GenerationBudget,
) -> None:
    """Explicitly replace a policy atomically with an owner-only file."""
    try:
        if type(relative_path) is not str or not relative_path or not root.is_absolute():
            raise ValueError
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError
        payload = dump_behavior_policy_yaml(policy, max_bytes=max_bytes, budget=budget)
        with atomic_binary_writer(root / path) as handle:
            handle.write(payload)
            budget.check("private policy publication")
        return
    except (OSError, ValueError):
        pass
    try:
        raise BehaviorPolicyError("invalid private policy file")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise
