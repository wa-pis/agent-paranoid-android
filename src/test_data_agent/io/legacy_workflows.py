"""Deprecated workflow shim; prefer test_data_agent.compat.legacy_workflows."""

from test_data_agent.compat.legacy_workflows import (
    _warn_deprecated_generation_spec_compatibility,
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)

__all__ = [
    "_warn_deprecated_generation_spec_compatibility",
    "generate_legacy_spec_artifacts",
    "validate_legacy_spec_artifacts",
]
