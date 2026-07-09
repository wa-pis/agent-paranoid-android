"""Safe synthetic test data generation.

The package root now exposes the domain-agnostic DatasetSpec pipeline first
while retaining legacy GenerationSpec symbols for compatibility.
"""

from test_data_agent.core import DatasetProfile, DatasetSpec
from test_data_agent.generation import generate_dataset, infer_dataset_spec, solve_constraints
from test_data_agent.generator import generate_rows, generate_tables
from test_data_agent.spec import ColumnSpec, ForeignKeySpec, GenerationSpec, MultiTableGenerationSpec, TableSpec
from test_data_agent.validation import DatasetValidationReport, validate_dataset
from test_data_agent.validator import validate_rows

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
