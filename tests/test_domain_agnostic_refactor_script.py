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
        "from test_data_agent.compat",
        False,
        "CLI imports deprecated workflows from the compat boundary",
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
        "src/test_data_agent/compat/legacy_workflows.py",
        "_warn_deprecated_generation_spec_compatibility",
        False,
        "compat-owned legacy workflows emit deprecated warnings",
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


def test_phase21_tracks_legacy_cli_command_boundary() -> None:
    module = load_refactor_module()

    phase21 = module.phase_by_id("phase21")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase21.text_checks
    }

    assert "src/test_data_agent/compat/commands.py" in phase21.expected_files
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.compat.commands import generate_legacy_command, validate_legacy_command",
        False,
        "CLI delegates deprecated command routing to compat command helpers",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "generate_legacy_spec_artifacts(",
        True,
        "CLI no longer orchestrates deprecated generation workflows directly",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "validate_legacy_spec_artifacts(",
        True,
        "CLI no longer orchestrates deprecated validation workflows directly",
    ) in checks


def test_phase21_runs_cli_compat_and_command_suites() -> None:
    module = load_refactor_module()

    phase21 = module.phase_by_id("phase21")

    assert phase21.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_cli.py",
            "tests/test_compat_legacy.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_io_commands.py"),
    )


def test_phase22_tracks_profile_example_command_boundary() -> None:
    module = load_refactor_module()

    phase22 = module.phase_by_id("phase22")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase22.text_checks
    }

    assert (
        "src/test_data_agent/cli.py",
        "profile_example_command,",
        False,
        "CLI imports the dataset-oriented profile-example command helper",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "return profile_example_command(args)",
        False,
        "CLI delegates profile-example to the command helper",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "profile_example_artifacts(",
        True,
        "CLI no longer orchestrates example profiling artifacts directly",
    ) in checks


def test_phase22_runs_cli_and_command_suites() -> None:
    module = load_refactor_module()

    phase22 = module.phase_by_id("phase22")

    assert phase22.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_cli.py",
            "tests/test_io_commands.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
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


def test_phase12_narrows_cli_compat_workflow_imports() -> None:
    module = load_refactor_module()

    phase12 = module.phase_by_id("phase12")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase12.text_checks
    }

    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.compat.",
        False,
        "CLI imports deprecated compatibility helpers from dedicated compat modules",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.compat import",
        True,
        "CLI no longer imports deprecated compatibility helpers from the compat package root",
    ) in checks


def test_phase12_runs_cli_and_compat_contract_suites() -> None:
    module = load_refactor_module()

    phase12 = module.phase_by_id("phase12")

    assert phase12.test_commands == (
        (module.PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_compat_legacy.py"),
    )


def test_phase13_routes_package_root_legacy_shims_through_compat() -> None:
    module = load_refactor_module()

    phase13 = module.phase_by_id("phase13")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase13.text_checks
    }

    assert "src/test_data_agent/compat/legacy_spec.py" in phase13.expected_files
    assert (
        "src/test_data_agent/__init__.py",
        "test_data_agent.compat.legacy_spec",
        False,
        "package root legacy shims resolve through the compat boundary",
    ) in checks


def test_phase16_tracks_dataset_command_helper_boundary() -> None:
    module = load_refactor_module()

    phase16 = module.phase_by_id("phase16")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase16.text_checks
    }

    assert "src/test_data_agent/io/commands.py" in phase16.expected_files
    assert (
        "src/test_data_agent/cli.py",
        "def is_dataset_spec_path(",
        True,
        "CLI no longer owns dataset-spec path detection",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "load_dataset_spec(",
        True,
        "CLI no longer loads dataset specs directly for dataset-oriented commands",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "validate_dataset(",
        True,
        "CLI no longer validates dataset-oriented rows directly",
    ) in checks


def test_phase16_runs_io_and_cli_focused_suites() -> None:
    module = load_refactor_module()

    phase16 = module.phase_by_id("phase16")

    assert phase16.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_io_commands.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
    )


def test_phase17_tracks_example_dataset_command_boundary() -> None:
    module = load_refactor_module()

    phase17 = module.phase_by_id("phase17")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase17.text_checks
    }

    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.io import (\n    generate_dataset_from_example_artifacts,",
        False,
        "CLI delegates example-dataset generation to io command helpers",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "profile_example_command,",
        False,
        "CLI delegates example-dataset profiling to io command helpers",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.profiling import profile_example_folder",
        True,
        "CLI no longer imports example-folder profiling directly",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "generate_dataset_review_artifacts(",
        True,
        "CLI no longer orchestrates example review bundles directly",
    ) in checks


def test_phase17_runs_example_command_and_cli_suites() -> None:
    module = load_refactor_module()

    phase17 = module.phase_by_id("phase17")

    assert phase17.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_io_commands.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_domain_agnostic_pipeline.py"),
    )


def test_phase18_tracks_single_input_profiling_command_boundary() -> None:
    module = load_refactor_module()

    phase18 = module.phase_by_id("phase18")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase18.text_checks
    }

    assert (
        "src/test_data_agent/cli.py",
        "infer_dataset_spec_command,",
        False,
        "CLI delegates infer-spec to io command helpers",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "profile_csv_command,",
        False,
        "CLI delegates profile-csv to io command helpers",
    ) in checks
    assert (
        "src/test_data_agent/cli.py",
        "from test_data_agent.adapters import load_profile_or_spec",
        True,
        "CLI no longer imports profile/spec loaders for dataset-oriented commands",
    ) in checks


def test_phase18_runs_single_input_command_and_cli_suites() -> None:
    module = load_refactor_module()

    phase18 = module.phase_by_id("phase18")

    assert phase18.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_io_commands.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py"),
    )


def test_phase19_moves_legacy_output_writers_into_compat() -> None:
    module = load_refactor_module()

    phase19 = module.phase_by_id("phase19")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase19.text_checks
    }

    assert "src/test_data_agent/compat/legacy_outputs.py" in phase19.expected_files
    assert (
        "src/test_data_agent/compat/legacy_workflows.py",
        "from test_data_agent.compat.legacy_outputs import",
        False,
        "compat workflows use compat-owned legacy output helpers",
    ) in checks
    assert (
        "src/test_data_agent/io/writers.py",
        "from test_data_agent.spec import GenerationSpec",
        True,
        "dataset-oriented writers no longer depend on GenerationSpec",
    ) in checks
    assert (
        "src/test_data_agent/io/artifacts.py",
        "from test_data_agent.spec import GenerationSpec",
        True,
        "dataset-oriented artifacts no longer depend on GenerationSpec",
    ) in checks


def test_phase19_runs_compat_and_io_focused_suites() -> None:
    module = load_refactor_module()

    phase19 = module.phase_by_id("phase19")

    assert phase19.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_compat_legacy.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
    )


def test_phase20_separates_legacy_profile_adapter_boundary() -> None:
    module = load_refactor_module()

    phase20 = module.phase_by_id("phase20")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase20.text_checks
    }

    assert "src/test_data_agent/adapters/legacy_profile.py" in phase20.expected_files
    assert (
        "src/test_data_agent/adapters/csv_file.py",
        "from test_data_agent.adapters.legacy_generation import",
        True,
        "CSV adapter no longer imports legacy generation helpers",
    ) in checks
    assert (
        "src/test_data_agent/adapters/json_profile.py",
        "from test_data_agent.adapters.legacy_generation import",
        True,
        "JSON adapter no longer imports legacy generation helpers",
    ) in checks
    assert (
        "src/test_data_agent/adapters/trino_profile.py",
        "from test_data_agent.adapters.legacy_generation import",
        True,
        "Trino adapter no longer imports legacy generation helpers",
    ) in checks
    assert (
        "src/test_data_agent/adapters/csv_file.py",
        "from test_data_agent.adapters.legacy_profile import",
        False,
        "CSV adapter imports dedicated legacy profile helpers",
    ) in checks
    assert (
        "src/test_data_agent/adapters/json_profile.py",
        "from test_data_agent.adapters.legacy_profile import",
        False,
        "JSON adapter imports dedicated legacy profile helpers",
    ) in checks
    assert (
        "src/test_data_agent/adapters/trino_profile.py",
        "from test_data_agent.adapters.legacy_profile import",
        False,
        "Trino adapter imports dedicated legacy profile helpers",
    ) in checks


def test_phase20_runs_adapter_and_contract_suites() -> None:
    module = load_refactor_module()

    phase20 = module.phase_by_id("phase20")

    assert phase20.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_source_adapters.py",
            "tests/test_domain_agnostic_refactor_script.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_dataset_spec_contract.py"),
    )


def test_phase13_runs_compat_and_package_root_contract_suites() -> None:
    module = load_refactor_module()

    phase13 = module.phase_by_id("phase13")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase13.text_checks
    }

    assert (
        "src/test_data_agent/compat/__init__.py",
        "from test_data_agent.compat.legacy_spec import",
        False,
        "compat package root re-exports deprecated legacy spec helpers explicitly",
    ) in checks

    assert phase13.test_commands == (
        (
            module.PYTHON,
            "-m",
            "pytest",
            "tests/test_compat_legacy.py",
            "tests/test_dataset_spec_contract.py",
        ),
        (module.PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
    )


def test_phase14_moves_business_rule_models_into_rules_package() -> None:
    module = load_refactor_module()

    phase14 = module.phase_by_id("phase14")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase14.text_checks
    }

    assert "src/test_data_agent/rules/models.py" in phase14.expected_files
    assert (
        "src/test_data_agent/rules/business_config.py",
        "from test_data_agent.rules.models import",
        False,
        "neutral business config helpers import rule models from the rules package",
    ) in checks
    assert (
        "src/test_data_agent/rules/scenarios.py",
        "from test_data_agent.rules.models import",
        False,
        "neutral scenario helpers import rule models from the rules package",
    ) in checks
    assert (
        "src/test_data_agent/rules/validation.py",
        "from test_data_agent.rules.models import",
        False,
        "neutral validation helpers import rule models from the rules package",
    ) in checks
    assert (
        "src/test_data_agent/business_rules.py",
        "from test_data_agent.rules.models import",
        False,
        "legacy business_rules module is a compatibility shim over the rules package",
    ) in checks


def test_phase14_runs_business_rules_and_refactor_contract_suites() -> None:
    module = load_refactor_module()

    phase14 = module.phase_by_id("phase14")

    assert phase14.test_commands == (
        (module.PYTHON, "-m", "pytest", "tests/test_business_rules.py"),
        (module.PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
    )


def test_phase15_moves_business_rule_application_into_rules_package() -> None:
    module = load_refactor_module()

    phase15 = module.phase_by_id("phase15")
    checks = {
        (check.path, check.text, check.absent, check.description)
        for check in phase15.text_checks
    }

    assert "src/test_data_agent/rules/engine.py" in phase15.expected_files
    assert (
        "src/test_data_agent/rules/business_config.py",
        "from test_data_agent.rules.engine import",
        False,
        "neutral business config helpers import rule application from the rules package",
    ) in checks
    assert (
        "src/test_data_agent/rules_engine.py",
        "from test_data_agent.rules.engine import",
        False,
        "legacy rules_engine module is a compatibility shim over the rules package",
    ) in checks
    assert (
        "src/test_data_agent/rules_engine.py",
        "from test_data_agent.rules.models import",
        True,
        "legacy rules_engine module no longer owns neutral rule implementation",
    ) in checks


def test_phase15_runs_business_rules_and_refactor_contract_suites() -> None:
    module = load_refactor_module()

    phase15 = module.phase_by_id("phase15")

    assert phase15.test_commands == (
        (module.PYTHON, "-m", "pytest", "tests/test_business_rules.py"),
        (module.PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
    )
