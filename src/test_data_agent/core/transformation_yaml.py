"""Restricted policy YAML bytes; never public summaries or execution approval."""

from typing import Any
from collections.abc import Hashable

import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.serialization import LimitedSafeLoader
from test_data_agent.core.transformation_policy import BehaviorPolicy, BehaviorPolicyError, parse_behavior_policy


class _PolicyLoader(LimitedSafeLoader):
    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Hashable, Any]:
        result: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str or key in result:
                raise ValueError("invalid policy key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_behavior_policy_yaml(payload: bytes, *, max_bytes: int, budget: GenerationBudget) -> BehaviorPolicy:
    """Bounded UTF-8 safe load; reject duplicate/non-string keys and YAML merges."""
    try:
        budget.check("policy YAML")
        if type(max_bytes) is not int or max_bytes < 1 or type(payload) is not bytes or len(payload) > max_bytes:
            raise ValueError
        loader = _PolicyLoader(payload.decode("utf-8"))
        try:
            raw = loader.get_single_data()
        finally:
            loader.dispose()  # type: ignore[no-untyped-call]
        result = parse_behavior_policy(raw)
        budget.check("policy YAML")
        return result
    except (ValueError, yaml.YAMLError):
        pass
    try:
        raise BehaviorPolicyError("invalid private policy YAML")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise


def dump_behavior_policy_yaml(policy: BehaviorPolicy, *, max_bytes: int, budget: GenerationBudget) -> bytes:
    """Produce restricted bytes only; caller must not expose them in summaries."""
    try:
        budget.check("policy YAML")
        if type(max_bytes) is not int or max_bytes < 1:
            raise ValueError
        validated = parse_behavior_policy(policy)
        payload = yaml.safe_dump(validated.model_dump(mode="json"), sort_keys=False, allow_unicode=True).encode("utf-8")
        if len(payload) > max_bytes:
            raise ValueError
        budget.check("policy YAML")
        return payload
    except (ValueError, yaml.YAMLError):
        pass
    try:
        raise BehaviorPolicyError("invalid private policy YAML")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise
