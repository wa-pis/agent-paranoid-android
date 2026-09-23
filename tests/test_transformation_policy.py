import copy

import pytest

from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy


def policy(behavior):
    return {"schema_version": "0.1", "schema_fingerprint": "a" * 64, "seed": 7,
            "fields": [{"entity": "items", "field": "value", "sensitivity": "non_sensitive",
                        "behavior": behavior}]}


@pytest.mark.parametrize("behavior", [
    {"action": "preserve", "authorization_ref": "user-review"},
    {"action": "synthesize", "generation_policy_ref": "amount-rule"},
    {"action": "substitute", "mapping": {"kind": "inline", "entries": [
        {"original": ["fictional-a"], "replacement": ["fictional-b"]}]}},
    {"action": "derive", "expression": "a + b", "dependencies": ["a", "b"]},
    {"action": "drop"},
])
def test_all_actions_roundtrip_privately(behavior):
    result = parse_behavior_policy(policy(behavior))
    assert parse_behavior_policy(result.model_dump(mode="json")) == result
    assert repr(result) == "BehaviorPolicy(schema_version='0.1')"


@pytest.mark.parametrize("change", ["version", "extra", "duplicate", "sensitivity", "missing_auth"])
def test_invalid_policy_is_value_free(change):
    payload = policy({"action": "preserve", "authorization_ref": "fictional-private-marker"})
    if change == "version":
        payload["schema_version"] = "fictional-private-marker"
    elif change == "extra":
        payload["fields"][0]["behavior"]["mapping"] = {}
    elif change == "duplicate":
        payload["fields"].append(copy.deepcopy(payload["fields"][0]))
    elif change == "sensitivity":
        payload["fields"][0]["sensitivity"] = "sensitive"
    else:
        del payload["fields"][0]["behavior"]["authorization_ref"]
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as error:
            parse_behavior_policy(payload)
    assert str(error.value) == "invalid behavior policy"
    assert error.value.__context__ is None


def test_domain_reference_must_resolve_and_cannot_chain():
    payload = policy({"action": "substitute", "mapping": {"kind": "domain", "name": "dates"}})
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)
    payload["domains"] = [{"name": "dates", "mapping": {"kind": "inline", "entries": [
        {"original": ["2025-04-30"], "replacement": ["2026-09-23"]}]}}]
    assert parse_behavior_policy(payload).fields[0].behavior.unmatched.action == "reject"
    payload["domains"][0]["mapping"] = {"kind": "domain", "name": "dates"}
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)


@pytest.mark.parametrize("sensitivity", ["non_sensitive", "sensitive", "unknown"])
def test_unmatched_preserve_requires_non_sensitive_declaration(sensitivity):
    payload = policy({"action": "substitute", "mapping": {"kind": "csv",
        "path": "fictional.csv", "source_columns": ["old"], "replacement_columns": ["new"]},
        "unmatched": {"action": "preserve", "authorization_ref": "review"}})
    payload["fields"][0]["sensitivity"] = sensitivity
    if sensitivity == "non_sensitive":
        assert parse_behavior_policy(payload).fields[0].behavior.unmatched.action == "preserve"
    else:
        with pytest.raises(BehaviorPolicyError):
            parse_behavior_policy(payload)


def test_required_version_and_unique_domains():
    payload = policy({"action": "drop"})
    del payload["schema_version"]
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)
    payload["schema_version"] = "0.1"
    domain = {"name": "dates", "mapping": {"kind": "inline", "entries": [
        {"original": ["a"], "replacement": ["b"]}]}}
    payload["domains"] = [domain, copy.deepcopy(domain)]
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)
