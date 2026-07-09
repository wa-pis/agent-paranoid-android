from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "domain_agnostic_refactor.py"


def load_refactor_module():
    spec = importlib.util.spec_from_file_location("domain_agnostic_refactor", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase7_tracks_remaining_legacy_workflow_boundary() -> None:
    module = load_refactor_module()

    phase7 = module.phase_by_id("phase7")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase7.text_checks
    }

    assert (
        "src/test_data_agent/io/workflows.py",
        "generate_legacy_compatibility_result",
        True,
        "workflow helpers no longer call legacy generation adapters",
    ) in checks
    assert (
        "src/test_data_agent/io/workflows.py",
        "validate_legacy_rows_file",
        True,
        "workflow helpers no longer call legacy validation adapters",
    ) in checks
    assert (
        "src/test_data_agent/io/workflows.py",
        "def generate_legacy_spec_artifacts(",
        True,
        "workflow helpers no longer expose legacy generation workflows",
    ) in checks
    assert (
        "src/test_data_agent/io/workflows.py",
        "def validate_legacy_spec_artifacts(",
        True,
        "workflow helpers no longer expose legacy validation workflows",
    ) in checks


def test_phase7_runs_refactor_script_contract_before_full_pytest() -> None:
    module = load_refactor_module()

    phase7 = module.phase_by_id("phase7")

    assert phase7.test_commands[0] == (
        module.PYTHON,
        "-m",
        "pytest",
        "tests/test_domain_agnostic_refactor_script.py",
    )
    assert phase7.test_commands[-1] == (module.PYTHON, "-m", "pytest")


def test_phase8_tracks_compatibility_boundary() -> None:
    module = load_refactor_module()

    phase8 = module.phase_by_id("phase8")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase8.text_checks
    }

    assert "src/test_data_agent/compat/__init__.py" in phase8.expected_files
    assert "src/test_data_agent/compat/legacy_generation.py" in phase8.expected_files
    assert "src/test_data_agent/compat/legacy_workflows.py" in phase8.expected_files
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.compat import",
        False,
        "CLI imports deprecated workflows from compat boundary",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.io.legacy_workflows import",
        True,
        "CLI no longer imports deprecated workflows from io package",
    ) in checks


def test_phase9_tracks_dataset_adapter_exports_boundary() -> None:
    module = load_refactor_module()

    phase9 = module.phase_by_id("phase9")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase9.text_checks
    }

    assert (
        "src/test_data_agent/adapters/__init__.py",
        "from test_data_agent.adapters.legacy_generation import",
        True,
        "adapter package root no longer re-exports deprecated GenerationSpec helpers",
    ) in checks
    assert (
        "tests/test_dataset_spec_contract.py",
        "from test_data_agent.adapters.legacy_generation import",
        False,
        "legacy adapter contract tests import deprecated conversions explicitly",
    ) in checks


def test_phase10_tracks_legacy_warning_boundary() -> None:
    module = load_refactor_module()

    phase10 = module.phase_by_id("phase10")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase10.text_checks
    }

    assert (
        "src/test_data_agent/io/workflows.py",
        "warn_deprecated_generation_spec_compatibility",
        True,
        "dataset-oriented workflows no longer carry deprecated warning helpers",
    ) in checks
    assert (
        "src/test_data_agent/io/legacy_workflows.py",
        "_warn_deprecated_generation_spec_compatibility",
        False,
        "legacy workflows own deprecated warning emission",
    ) in checks


def test_phase10_runs_focused_workflow_and_cli_suites() -> None:
    module = load_refactor_module()

    phase10 = module.phase_by_id("phase10")

    assert phase10.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_io_workflows.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py"),
    )


def test_phase11_tracks_compat_owned_legacy_workflow_implementation() -> None:
    module = load_refactor_module()

    phase11 = module.phase_by_id("phase11")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase11.text_checks
    }

    assert (
        "src/test_data_agent/compat/legacy_workflows.py",
        "def generate_legacy_spec_artifacts(",
        False,
        "compat workflows own deprecated generation implementation",
    ) in checks
    assert (
        "src/test_data_agent/compat/legacy_workflows.py",
        "def validate_legacy_spec_artifacts(",
        False,
        "compat workflows own deprecated validation implementation",
    ) in checks
    assert (
        "src/test_data_agent/io/legacy_workflows.py",
        "generate_legacy_compatibility_result",
        True,
        "io legacy workflow shim no longer implements deprecated generation flow",
    ) in checks
    assert (
        "src/test_data_agent/io/legacy_workflows.py",
        "_warn_deprecated_generation_spec_compatibility",
        True,
        "io legacy workflow shim no longer owns deprecated warning logic",
    ) in checks


def test_phase11_runs_compat_and_cli_focused_suites() -> None:
    module = load_refactor_module()

    phase11 = module.phase_by_id("phase11")

    assert phase11.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_compat_legacy.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
    )
