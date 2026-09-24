import stat

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy
from test_data_agent.io.behavior_policy_files import load_behavior_policy_file, save_behavior_policy_file


def policy():
    return parse_behavior_policy({"schema_version": "0.1", "schema_fingerprint": "a" * 64,
        "seed": 7, "fields": [{"entity": "items", "field": "value", "sensitivity": "unknown",
                               "behavior": {"action": "drop"}}]})


def test_private_policy_file_roundtrip_and_permissions(tmp_path):
    root = tmp_path.resolve()
    original = policy()
    save_behavior_policy_file(root, "policy.yaml", original, max_bytes=10000, budget=GenerationBudget())
    assert load_behavior_policy_file(root, "policy.yaml", max_bytes=10000, budget=GenerationBudget()) == original
    assert stat.S_IMODE((root / "policy.yaml").stat().st_mode) & 0o077 == 0


@pytest.mark.parametrize("failure", ["limit", "deadline", "symlink", "escape"])
def test_failed_policy_save_preserves_existing_file(tmp_path, failure):
    root = tmp_path.resolve()
    destination = root / "policy.yaml"
    destination.write_bytes(b"existing")
    name, limit = "policy.yaml", 10000
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    if failure == "limit":
        limit = 1
    elif failure == "deadline":
        tick[0] = 2.0
    elif failure == "symlink":
        (root / "linked.yaml").symlink_to(destination)
        name = "linked.yaml"
    else:
        name = "../policy.yaml"
    with pytest.raises(BehaviorPolicyError, match="^invalid private policy file$") as caught:
        save_behavior_policy_file(root, name, policy(), max_bytes=limit, budget=budget)
    assert caught.value.__context__ is None
    assert destination.read_bytes() == b"existing"
    assert not list(root.glob(".*.tmp"))


def test_deadline_before_publication_rolls_back_temporary_file(tmp_path):
    root = tmp_path.resolve()
    destination = root / "policy.yaml"
    destination.write_bytes(b"existing")
    calls = [0]

    def clock():
        calls[0] += 1
        return 2.0 if calls[0] >= 4 else 0.0

    with pytest.raises(BehaviorPolicyError):
        save_behavior_policy_file(root, "policy.yaml", policy(), max_bytes=10000,
                                  budget=GenerationBudget(max_seconds=1, clock=clock))
    assert destination.read_bytes() == b"existing"
    assert not list(root.glob(".*.tmp"))


@pytest.mark.parametrize("failure", ["missing", "malformed", "symlink"])
def test_private_policy_load_errors_do_not_retain_values(tmp_path, failure):
    root = tmp_path.resolve()
    name = "fictional-private-marker.yaml"
    if failure != "missing":
        (root / name).write_bytes(b"!!bool fictional-private-marker")
    if failure == "symlink":
        (root / "linked.yaml").symlink_to(root / name)
        name = "linked.yaml"
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as caught:
            load_behavior_policy_file(root, name, max_bytes=1000, budget=GenerationBudget())
    assert str(caught.value) == "invalid private policy file"
    assert caught.value.__context__ is None
