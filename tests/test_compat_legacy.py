from test_data_agent import compat
from test_data_agent.adapters import legacy_generation as adapter_legacy_generation
from test_data_agent.io import legacy_workflows as io_legacy_workflows


def test_compat_package_exposes_deprecated_generation_helpers() -> None:
    assert compat.generation_spec_to_dataset_spec is adapter_legacy_generation.generation_spec_to_dataset_spec
    assert compat.generate_legacy_rows is adapter_legacy_generation.generate_legacy_rows
    assert compat.validate_legacy_rows_report is adapter_legacy_generation.validate_legacy_rows_report


def test_compat_package_exposes_deprecated_workflow_helpers() -> None:
    assert compat.generate_legacy_spec_artifacts is io_legacy_workflows.generate_legacy_spec_artifacts
    assert compat.validate_legacy_spec_artifacts is io_legacy_workflows.validate_legacy_spec_artifacts
