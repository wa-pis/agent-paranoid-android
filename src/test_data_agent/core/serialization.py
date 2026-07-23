"""Bounded parsers for untrusted structured inputs."""

from __future__ import annotations

from typing import Any

import yaml
from yaml.events import AliasEvent

from test_data_agent.core.limits import max_yaml_aliases, max_yaml_depth


class LimitedSafeLoader(yaml.SafeLoader):
    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self.alias_count = 0
        self.composition_depth = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        event = self.peek_event()  # type: ignore[no-untyped-call]
        if isinstance(event, AliasEvent):
            self.alias_count += 1
            if self.alias_count > max_yaml_aliases():
                raise ValueError(f"YAML input contains more than {max_yaml_aliases()} aliases")
        self.composition_depth += 1
        try:
            if self.composition_depth > max_yaml_depth():
                raise ValueError(f"YAML input nesting exceeds {max_yaml_depth()} levels")
            return super().compose_node(parent, index)
        finally:
            self.composition_depth -= 1


def load_limited_yaml(text: str) -> Any:
    loader = LimitedSafeLoader(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()  # type: ignore[no-untyped-call]
