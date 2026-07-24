"""Safe synthetic test data generation."""

from __future__ import annotations

from test_data_agent.agent import (
    AgentRequest,
    AgentResult,
    AgentSourceType,
    approve_agent_workspace,
    plan_agent_profile,
    plan_agent_request,
)
from test_data_agent.core import DATASET_SPEC_SCHEMA_VERSION, DatasetProfile, DatasetSpec
from test_data_agent.generation import generate_dataset, infer_dataset_spec, solve_constraints
from test_data_agent.io.workflows import DatasetGenerationResult, generate_dataset_bundle
from test_data_agent.validation import DatasetValidationReport, validate_dataset
from test_data_agent.version import __version__

__all__ = [
    "AgentRequest",
    "AgentResult",
    "AgentSourceType",
    "DatasetProfile",
    "DatasetSpec",
    "DatasetGenerationResult",
    "DatasetValidationReport",
    "DATASET_SPEC_SCHEMA_VERSION",
    "approve_agent_workspace",
    "generate_dataset",
    "generate_dataset_bundle",
    "infer_dataset_spec",
    "plan_agent_request",
    "plan_agent_profile",
    "solve_constraints",
    "validate_dataset",
    "__version__",
]
