"""Bounded parsers for untrusted structured inputs."""

from __future__ import annotations

import json
from typing import Any

import yaml
from yaml.events import AliasEvent
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from test_data_agent.core.limits import (
    InputLimitError,
    max_json_depth,
    max_input_cells,
    max_input_file_bytes,
    max_yaml_aliases,
    max_yaml_depth,
)


class LimitedSafeLoader(yaml.SafeLoader):
    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self.alias_count = 0
        self.composition_depth = 0
        self._expanded_sizes: dict[int, tuple[int, int]] = {}
        self._alias_nodes = 0

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
            node = super().compose_node(parent, index)
            if isinstance(event, AliasEvent):
                if id(node) not in self._expanded_sizes:
                    raise InputLimitError("recursive YAML aliases are not allowed")
                self._alias_nodes += self._expanded_sizes[id(node)][0]
                if self._alias_nodes > max_input_cells():
                    raise InputLimitError("YAML logical expansion exceeds configured input limits")
                return node
            nodes, byte_count = 1, 0
            if isinstance(node, ScalarNode):
                byte_count = len(node.value.encode("utf-8"))
                children = []
            elif isinstance(node, SequenceNode):
                children = node.value
            elif isinstance(node, MappingNode):
                children = [child for pair in node.value for child in pair]
            else:
                raise InputLimitError("unsupported YAML node")
            for child in children:
                child_nodes, child_bytes = self._expanded_sizes[id(child)]
                nodes += child_nodes
                byte_count += child_bytes
            if byte_count > max_input_file_bytes():
                raise InputLimitError("YAML logical expansion exceeds configured input limits")
            self._expanded_sizes[id(node)] = nodes, byte_count
            return node
        finally:
            self.composition_depth -= 1


def load_limited_yaml(text: str) -> Any:
    loader = LimitedSafeLoader(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()  # type: ignore[no-untyped-call]


def load_limited_json(text: str, *, label: str = "JSON input") -> Any:
    """Reject excessive structural depth before materializing JSON."""
    depth = 0
    in_string = False
    escaped = False
    depth_limit = max_json_depth()

    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > depth_limit:
                raise InputLimitError(f"{label} must have depth <= {depth_limit}")
        elif character in "]}":
            depth = max(0, depth - 1)

    return json.loads(text)
