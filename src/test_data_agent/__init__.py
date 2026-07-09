"""Safe synthetic test data generation.

The package root now exposes the domain-agnostic DatasetSpec pipeline first
while retaining legacy GenerationSpec symbols for compatibility.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any
from warnings import warn

from test_data_agent.core import DatasetProfile, DatasetSpec
from test_data_agent.generation import generate_dataset, infer_dataset_spec, solve_constraints
from test_data_agent.validation import DatasetValidationReport, validate_dataset

_LEGACY_EXPORTS = {
    "ColumnSpec": ("test_data_agent.compat.legacy_spec", "ColumnSpec"),
    "ForeignKeySpec": ("test_data_agent.compat.legacy_spec", "ForeignKeySpec"),
    "GenerationSpec": ("test_data_agent.compat.legacy_spec", "GenerationSpec"),
    "MultiTableGenerationSpec": ("test_data_agent.compat.legacy_spec", "MultiTableGenerationSpec"),
    "TableSpec": ("test_data_agent.compat.legacy_spec", "TableSpec"),
    "generate_rows": ("test_data_agent.compat.legacy_spec", "generate_rows"),
    "generate_tables": ("test_data_agent.compat.legacy_spec", "generate_tables"),
    "validate_rows": ("test_data_agent.compat.legacy_spec", "validate_rows"),
}

__all__ = [
    "DatasetProfile",
    "DatasetSpec",
    "DatasetValidationReport",
    "ColumnSpec",
    "ForeignKeySpec",
    "GenerationSpec",
    "MultiTableGenerationSpec",
    "TableSpec",
    "generate_dataset",
    "infer_dataset_spec",
    "solve_constraints",
    "generate_rows",
    "generate_tables",
    "validate_dataset",
    "validate_rows",
]


def __getattr__(name: str) -> Any:
    legacy_target = _LEGACY_EXPORTS.get(name)
    if legacy_target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    warn(
        f"test_data_agent.{name} is deprecated; import DatasetSpec APIs from dedicated modules instead",
        DeprecationWarning,
        stacklevel=2,
    )
    module_name, attribute_name = legacy_target
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
