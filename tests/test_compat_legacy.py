from test_data_agent import compat
from test_data_agent.adapters import legacy_generation as adapter_legacy_generation
from test_data_agent.compat import legacy_outputs as compat_legacy_outputs
from test_data_agent.compat import legacy_spec as compat_legacy_spec
from test_data_agent.io import legacy_workflows as io_legacy_workflows
from test_data_agent.spec import (
    ColumnSpec,
    ForeignKeySpec,
    GenerationSpec,
    MultiTableGenerationSpec,
    TableSpec,
)
from test_data_agent.generator import generate_rows, generate_tables
from test_data_agent.validator import validate_rows


def test_compat_package_exposes_deprecated_spec_and_row_helpers() -> None:
    assert compat.ColumnSpec is ColumnSpec
    assert compat.ForeignKeySpec is ForeignKeySpec
    assert compat.GenerationSpec is GenerationSpec
    assert compat.MultiTableGenerationSpec is MultiTableGenerationSpec
    assert compat.TableSpec is TableSpec
    assert compat.generate_rows is generate_rows
    assert compat.generate_tables is generate_tables
    assert compat.validate_rows is validate_rows
    assert compat_legacy_spec.GenerationSpec is GenerationSpec


def test_compat_package_exposes_deprecated_generation_helpers() -> None:
    assert compat.generation_spec_to_dataset_spec is adapter_legacy_generation.generation_spec_to_dataset_spec
    assert compat.generate_legacy_rows is adapter_legacy_generation.generate_legacy_rows
    assert compat.validate_legacy_rows_report is adapter_legacy_generation.validate_legacy_rows_report


def test_compat_package_exposes_deprecated_workflow_helpers() -> None:
    assert compat.generate_legacy_spec_artifacts is io_legacy_workflows.generate_legacy_spec_artifacts
    assert compat.validate_legacy_spec_artifacts is io_legacy_workflows.validate_legacy_spec_artifacts


def test_compat_legacy_outputs_module_owns_deprecated_row_and_artifact_writers() -> None:
    assert compat_legacy_outputs.write_tabular_rows.__module__ == "test_data_agent.compat.legacy_outputs"
    assert compat_legacy_outputs.write_generation_artifacts.__module__ == "test_data_agent.compat.legacy_outputs"
