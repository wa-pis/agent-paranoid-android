"""Deprecated workflow shim; prefer test_data_agent.compat.legacy_workflows."""

from test_data_agent.compat.legacy_workflows import (
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)

__all__ = [
    "generate_legacy_spec_artifacts",
    "validate_legacy_spec_artifacts",
]
