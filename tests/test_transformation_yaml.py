import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml, load_behavior_policy_yaml


def test_private_yaml_roundtrip_preserves_mapping_scalar_kinds():
    values = [True, 1, 1.0, "001", "2025-04-30", None, ""]
    policy = parse_behavior_policy({"schema_version": "0.1", "schema_fingerprint": "a" * 64,
        "seed": 7, "fields": [{"entity": "items", "field": "value", "sensitivity": "unknown",
        "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
            {"original": values, "replacement": values}]}}}]})
    budget = GenerationBudget()
    payload = dump_behavior_policy_yaml(policy, max_bytes=10000, budget=budget)
    restored = load_behavior_policy_yaml(payload, max_bytes=10000, budget=budget)
    assert restored == policy
    result = restored.fields[0].behavior.mapping.entries[0].original
    assert list(map(type, result)) == list(map(type, values))


@pytest.mark.parametrize("payload", [b"schema_version: '0.1'\nschema_version: '0.2'\n",
    b"!!python/object/apply:os.system ['fictional']", b"a: [", b"\xff",
    b"a: &a {x: 1}\nb: {<<: *a}", b"1: value", b"a: &a [*a]",
    b"!!bool fictional-private-marker", b"!!timestamp fictional-private-marker",
    b"!!map [fictional-private-marker]", b"!!set [fictional-private-marker]"])
def test_invalid_private_yaml_is_detached(payload):
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as caught:
            load_behavior_policy_yaml(payload, max_bytes=1000, budget=GenerationBudget())
    assert str(caught.value) == "invalid private policy YAML"
    assert caught.value.__context__ is None


def test_private_yaml_input_byte_ceiling():
    with pytest.raises(BehaviorPolicyError):
        load_behavior_policy_yaml(b"a: long", max_bytes=1, budget=GenerationBudget())


def test_private_yaml_rejects_nested_duplicate_keys():
    payload = b"fields:\n  - behavior:\n      action: drop\n      action: preserve\n"
    with pytest.raises(BehaviorPolicyError, match="^invalid private policy YAML$"):
        load_behavior_policy_yaml(payload, max_bytes=1000, budget=GenerationBudget())


@pytest.mark.parametrize("failure", ["output_limit", "expired", "forged"])
def test_private_yaml_dump_errors_are_detached(failure):
    policy = parse_behavior_policy({"schema_version": "0.1", "schema_fingerprint": "a" * 64,
        "seed": 7, "fields": [{"entity": "items", "field": "value", "sensitivity": "unknown",
                               "behavior": {"action": "drop"}}]})
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    if failure == "expired":
        tick[0] = 2.0
    if failure == "forged":
        policy = policy.model_copy(update={"seed": "fictional-private-marker"})
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as caught:
            dump_behavior_policy_yaml(policy, max_bytes=1 if failure == "output_limit" else 10000,
                                      budget=budget)
    assert str(caught.value) == "invalid private policy YAML"
    assert caught.value.__context__ is None
