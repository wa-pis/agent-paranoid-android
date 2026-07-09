"""Compatibility re-exports for deprecated GenerationSpec CLI workflows."""

from test_data_agent.io.legacy_workflows import (
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)

__all__ = [
    "generate_legacy_spec_artifacts",
    "validate_legacy_spec_artifacts",
]
