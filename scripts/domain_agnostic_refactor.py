#!/usr/bin/env python3
"""Automation helper for the DatasetSpec refactoring.

The script is intentionally conservative. It does not rewrite production code.
It tracks expected phase files, reports missing migration pieces, and runs the
focused test commands that keep the refactor safe.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "docs" / "domain_agnostic_refactoring_plan.md"


@dataclass(frozen=True)
class TextCheck:
    path: str
    text: str
    description: str
    absent: bool = False


@dataclass(frozen=True)
class Phase:
    phase_id: str
    title: str
    goal: str
    expected_files: tuple[str, ...] = ()
    text_checks: tuple[TextCheck, ...] = ()
    test_commands: tuple[tuple[str, ...], ...] = ()


PYTHON = sys.executable


PHASES: tuple[Phase, ...] = (
    Phase(
        phase_id="phase0",
        title="Preserve plan and automation",
        goal="Keep the architecture review and refactoring automation in the repository.",
        expected_files=(
            "docs/domain_agnostic_refactoring_plan.md",
            "scripts/domain_agnostic_refactor.py",
        ),
        test_commands=((PYTHON, "scripts/domain_agnostic_refactor.py", "check", "--phase", "phase0", "--strict"),),
    ),
    Phase(
        phase_id="phase1",
        title="Stabilize DatasetSpec contract",
        goal="Add typed distributions, privacy rules, and defaulted generation/validation settings.",
        expected_files=(
            "src/test_data_agent/core/distribution.py",
            "src/test_data_agent/core/privacy.py",
            "src/test_data_agent/core/settings.py",
        ),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/core/dataset.py",
                text="privacy_rules",
                description="DatasetSpec exposes privacy rules",
            ),
            TextCheck(
                path="src/test_data_agent/core/dataset.py",
                text="generation_settings",
                description="DatasetSpec exposes generation settings",
            ),
            TextCheck(
                path="src/test_data_agent/core/dataset.py",
                text="validation_settings",
                description="DatasetSpec exposes validation settings",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_dataset_spec_contract.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_pipeline.py"),
        ),
    ),
    Phase(
        phase_id="phase2",
        title="Centralize privacy policy",
        goal="Route sensitive detection, masking, and safe value exposure through one module.",
        expected_files=("src/test_data_agent/core/privacy.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/csv_profiler.py",
                text="from test_data_agent.core.privacy",
                description="single CSV profiler uses shared privacy policy",
            ),
            TextCheck(
                path="src/test_data_agent/profiling/schema_profiler.py",
                text="from test_data_agent.core.privacy",
                description="CSV-folder profiler uses shared privacy policy",
            ),
            TextCheck(
                path="src/test_data_agent/mcp_trino_server.py",
                text="from test_data_agent.core.privacy",
                description="Trino MCP safety uses shared privacy policy",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_csv_profiler.py"),
            (PYTHON, "-m", "pytest", "tests/test_mcp_trino_server.py"),
        ),
    ),
    Phase(
        phase_id="phase3",
        title="Introduce source adapters",
        goal="Normalize all supported source inputs into DatasetProfile or DatasetSpec.",
        expected_files=(
            "src/test_data_agent/adapters/__init__.py",
            "src/test_data_agent/adapters/csv_file.py",
            "src/test_data_agent/adapters/csv_folder.py",
            "src/test_data_agent/adapters/trino_profile.py",
            "src/test_data_agent/adapters/json_profile.py",
            "src/test_data_agent/adapters/parquet_dataset.py",
            "src/test_data_agent/adapters/legacy_generation.py",
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_source_adapters.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_pipeline.py"),
        ),
    ),
    Phase(
        phase_id="phase4",
        title="Migrate CSV flows",
        goal="Make profile-csv and generate-from-csv use one-entity DatasetSpec internally.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="GenerationSpec.from_csv_profile",
                description="legacy CSV spec inference removed from CLI",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_csv_profiler.py", "tests/test_generator.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_pipeline.py"),
        ),
    ),
    Phase(
        phase_id="phase5",
        title="Decouple business rules",
        goal="Move safe expressions and conditions into neutral rules modules.",
        expected_files=(
            "src/test_data_agent/rules/expressions.py",
            "src/test_data_agent/rules/conditions.py",
            "src/test_data_agent/rules/business_config.py",
        ),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/generation/constraint_solver.py",
                text="from test_data_agent.business_validator",
                description="generation no longer imports business validator",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/validation/constraint_validator.py",
                text="from test_data_agent.business_validator",
                description="validation no longer imports business validator",
                absent=True,
            ),
        ),
        test_commands=((PYTHON, "-m", "pytest", "tests/test_business_rules.py", "tests/test_domain_agnostic_pipeline.py"),),
    ),
    Phase(
        phase_id="phase6",
        title="Thin CLI",
        goal="Move readers, writers, artifact writing, and workflow orchestration out of cli.py.",
        expected_files=(
            "src/test_data_agent/io/readers.py",
            "src/test_data_agent/io/writers.py",
            "src/test_data_agent/io/artifacts.py",
        ),
        test_commands=(
            (
                PYTHON,
                "-m",
                "pytest",
                "tests/test_cli.py",
                "tests/test_domain_agnostic_pipeline.py",
                "tests/test_io_workflows.py",
            ),
        ),
    ),
    Phase(
        phase_id="phase7",
        title="Deprecate legacy spec path",
        goal="Remove legacy generators only after adapters and compatibility tests are stable.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.generator import generate_rows",
                description="CLI no longer imports legacy row generator",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.validator import validate_rows_report",
                description="CLI no longer imports legacy row validator directly",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="def build_generation_spec(",
                description="CLI no longer owns legacy GenerationSpec preparation",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="prepare_legacy_generation_spec",
                description="CLI no longer prepares legacy GenerationSpec objects directly",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="validate_legacy_rows_report",
                description="CLI no longer validates legacy rows from loaded JSON directly",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/workflows.py",
                text="generate_legacy_compatibility_result",
                description="workflow helpers no longer call legacy generation adapters",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/workflows.py",
                text="validate_legacy_rows_file",
                description="workflow helpers no longer call legacy validation adapters",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/workflows.py",
                text="def generate_legacy_spec_artifacts(",
                description="workflow helpers no longer expose legacy generation workflows",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/workflows.py",
                text="def validate_legacy_spec_artifacts(",
                description="workflow helpers no longer expose legacy validation workflows",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest"),
        ),
    ),
    Phase(
        phase_id="phase8",
        title="Isolate deprecated compatibility surface",
        goal="Route deprecated GenerationSpec helpers through a dedicated compat package.",
        expected_files=(
            "src/test_data_agent/compat/__init__.py",
            "src/test_data_agent/compat/legacy_generation.py",
            "src/test_data_agent/compat/legacy_workflows.py",
        ),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.compat",
                description="CLI imports deprecated workflows from the compat boundary",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.io.legacy_workflows import",
                description="CLI no longer imports deprecated workflows from io package",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_compat_legacy.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_source_adapters.py"),
        ),
    ),
    Phase(
        phase_id="phase9",
        title="Tighten dataset adapter exports",
        goal="Keep deprecated GenerationSpec conversions out of the dataset-oriented adapters package root.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/adapters/__init__.py",
                text="from test_data_agent.adapters.legacy_generation import",
                description="adapter package root no longer re-exports deprecated GenerationSpec helpers",
                absent=True,
            ),
            TextCheck(
                path="tests/test_dataset_spec_contract.py",
                text="from test_data_agent.adapters.legacy_generation import",
                description="legacy adapter contract tests import deprecated conversions explicitly",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_source_adapters.py", "tests/test_dataset_spec_contract.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
        ),
    ),
    Phase(
        phase_id="phase10",
        title="Detach legacy workflow warnings",
        goal="Keep deprecated GenerationSpec warnings inside legacy workflow modules instead of dataset-oriented workflow helpers.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/io/workflows.py",
                text="warn_deprecated_generation_spec_compatibility",
                description="dataset-oriented workflows no longer carry deprecated warning helpers",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/compat/legacy_workflows.py",
                text="_warn_deprecated_generation_spec_compatibility",
                description="compat-owned legacy workflows emit deprecated warnings",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_io_workflows.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py"),
        ),
    ),
    Phase(
        phase_id="phase11",
        title="Move legacy workflow implementation to compat",
        goal="Keep deprecated GenerationSpec workflow implementation inside compat modules while io only provides a thin shim.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/compat/legacy_workflows.py",
                text="def generate_legacy_spec_artifacts(",
                description="compat workflows own deprecated generation implementation",
            ),
            TextCheck(
                path="src/test_data_agent/compat/legacy_workflows.py",
                text="def validate_legacy_spec_artifacts(",
                description="compat workflows own deprecated validation implementation",
            ),
            TextCheck(
                path="src/test_data_agent/io/legacy_workflows.py",
                text="generate_legacy_compatibility_result",
                description="io legacy workflow shim no longer implements deprecated generation flow",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/legacy_workflows.py",
                text="_warn_deprecated_generation_spec_compatibility",
                description="io legacy workflow shim no longer owns deprecated warning logic",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_compat_legacy.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
        ),
    ),
    Phase(
        phase_id="phase12",
        title="Narrow compat workflow imports",
        goal="Keep deprecated workflow usage pointed at dedicated compat modules instead of the broad compat package root.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.compat.",
                description="CLI imports deprecated compatibility helpers from dedicated compat modules",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.compat import",
                description="CLI no longer imports deprecated compatibility helpers from the compat package root",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_compat_legacy.py"),
        ),
    ),
    Phase(
        phase_id="phase13",
        title="Route package-root legacy shims through compat",
        goal="Keep deprecated package-root symbols behind explicit compat modules instead of importing legacy modules directly.",
        expected_files=("src/test_data_agent/compat/legacy_spec.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/__init__.py",
                text="test_data_agent.compat.legacy_spec",
                description="package root legacy shims resolve through the compat boundary",
            ),
            TextCheck(
                path="src/test_data_agent/compat/__init__.py",
                text="from test_data_agent.compat.legacy_spec import",
                description="compat package root re-exports deprecated legacy spec helpers explicitly",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_compat_legacy.py", "tests/test_dataset_spec_contract.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
        ),
    ),
    Phase(
        phase_id="phase14",
        title="Move business rule models into rules package",
        goal="Keep neutral rule models and loaders in rules/ while business_rules.py becomes a compatibility shim.",
        expected_files=("src/test_data_agent/rules/models.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/rules/business_config.py",
                text="from test_data_agent.rules.models import",
                description="neutral business config helpers import rule models from the rules package",
            ),
            TextCheck(
                path="src/test_data_agent/rules/scenarios.py",
                text="from test_data_agent.rules.models import",
                description="neutral scenario helpers import rule models from the rules package",
            ),
            TextCheck(
                path="src/test_data_agent/rules/validation.py",
                text="from test_data_agent.rules.models import",
                description="neutral validation helpers import rule models from the rules package",
            ),
            TextCheck(
                path="src/test_data_agent/business_rules.py",
                text="from test_data_agent.rules.models import",
                description="legacy business_rules module is a compatibility shim over the rules package",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_business_rules.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
        ),
    ),
    Phase(
        phase_id="phase15",
        title="Move business rule application into rules package",
        goal="Keep neutral rule application in rules/ while rules_engine.py becomes a compatibility shim.",
        expected_files=("src/test_data_agent/rules/engine.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/rules/business_config.py",
                text="from test_data_agent.rules.engine import",
                description="neutral business config helpers import rule application from the rules package",
            ),
            TextCheck(
                path="src/test_data_agent/rules_engine.py",
                text="from test_data_agent.rules.engine import",
                description="legacy rules_engine module is a compatibility shim over the rules package",
            ),
            TextCheck(
                path="src/test_data_agent/rules_engine.py",
                text="from test_data_agent.rules.models import",
                description="legacy rules_engine module no longer owns neutral rule implementation",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_business_rules.py"),
            (PYTHON, "-m", "pytest", "tests/test_domain_agnostic_refactor_script.py"),
        ),
    ),
    Phase(
        phase_id="phase16",
        title="Extract dataset command helpers from CLI",
        goal="Keep dataset-spec path detection and orchestration in io helpers while cli.py focuses on parsing and command routing.",
        expected_files=("src/test_data_agent/io/commands.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.io import (\n    generate_dataset_from_csv_artifacts,\n    generate_dataset_from_profile_artifacts,\n    generate_dataset_from_spec_path,",
                description="CLI delegates dataset-spec generation to io command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="def is_dataset_spec_path(",
                description="CLI no longer owns dataset-spec path detection",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="load_dataset_spec(",
                description="CLI no longer loads dataset specs directly for dataset-oriented commands",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="validate_dataset(",
                description="CLI no longer validates dataset-oriented rows directly",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_io_commands.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
        ),
    ),
    Phase(
        phase_id="phase17",
        title="Extract example dataset commands from CLI",
        goal="Keep example-folder profiling and review-bundle orchestration in io helpers while cli.py only routes arguments.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.io import (\n    generate_dataset_from_example_artifacts,",
                description="CLI delegates example-dataset generation to io command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="profile_example_command,",
                description="CLI delegates example-dataset profiling to io command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.profiling import profile_example_folder",
                description="CLI no longer imports example-folder profiling directly",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="generate_dataset_review_artifacts(",
                description="CLI no longer orchestrates example review bundles directly",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_io_commands.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_domain_agnostic_pipeline.py"),
        ),
    ),
    Phase(
        phase_id="phase18",
        title="Extract single-input profiling commands from CLI",
        goal="Keep single-input profiling and profile-to-spec orchestration in io helpers while cli.py only routes arguments.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="infer_dataset_spec_command,",
                description="CLI delegates infer-spec to io command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="profile_csv_command,",
                description="CLI delegates profile-csv to io command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.adapters import load_profile_or_spec",
                description="CLI no longer imports profile/spec loaders for dataset-oriented commands",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_io_commands.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py"),
        ),
    ),
    Phase(
        phase_id="phase19",
        title="Move legacy output writers into compat",
        goal="Keep deprecated GenerationSpec row-output and artifact-writing helpers inside compat modules instead of dataset-oriented io helpers.",
        expected_files=("src/test_data_agent/compat/legacy_outputs.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/compat/legacy_workflows.py",
                text="from test_data_agent.compat.legacy_outputs import",
                description="compat workflows use compat-owned legacy output helpers",
            ),
            TextCheck(
                path="src/test_data_agent/io/writers.py",
                text="from test_data_agent.spec import GenerationSpec",
                description="dataset-oriented writers no longer depend on GenerationSpec",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/io/artifacts.py",
                text="from test_data_agent.spec import GenerationSpec",
                description="dataset-oriented artifacts no longer depend on GenerationSpec",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_compat_legacy.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_workflows.py"),
        ),
    ),
    Phase(
        phase_id="phase20",
        title="Separate legacy profile adapters",
        goal="Keep dataset-oriented legacy profile normalization separate from deprecated GenerationSpec workflow helpers.",
        expected_files=("src/test_data_agent/adapters/legacy_profile.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/adapters/csv_file.py",
                text="from test_data_agent.adapters.legacy_generation import",
                description="CSV adapter no longer imports legacy generation helpers",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/adapters/json_profile.py",
                text="from test_data_agent.adapters.legacy_generation import",
                description="JSON adapter no longer imports legacy generation helpers",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/adapters/trino_profile.py",
                text="from test_data_agent.adapters.legacy_generation import",
                description="Trino adapter no longer imports legacy generation helpers",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/adapters/csv_file.py",
                text="from test_data_agent.adapters.legacy_profile import",
                description="CSV adapter imports dedicated legacy profile helpers",
            ),
            TextCheck(
                path="src/test_data_agent/adapters/json_profile.py",
                text="from test_data_agent.adapters.legacy_profile import",
                description="JSON adapter imports dedicated legacy profile helpers",
            ),
            TextCheck(
                path="src/test_data_agent/adapters/trino_profile.py",
                text="from test_data_agent.adapters.legacy_profile import",
                description="Trino adapter imports dedicated legacy profile helpers",
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_source_adapters.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_dataset_spec_contract.py"),
        ),
    ),
    Phase(
        phase_id="phase21",
        title="Extract legacy command helpers from CLI",
        goal="Keep deprecated GenerationSpec CLI command orchestration in compat helpers while cli.py only routes arguments.",
        expected_files=("src/test_data_agent/compat/commands.py",),
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="from test_data_agent.compat.commands import generate_legacy_command, validate_legacy_command",
                description="CLI delegates deprecated command routing to compat command helpers",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="generate_legacy_spec_artifacts(",
                description="CLI no longer orchestrates deprecated generation workflows directly",
                absent=True,
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="validate_legacy_spec_artifacts(",
                description="CLI no longer orchestrates deprecated validation workflows directly",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_compat_legacy.py", "tests/test_domain_agnostic_refactor_script.py"),
            (PYTHON, "-m", "pytest", "tests/test_io_commands.py"),
        ),
    ),
    Phase(
        phase_id="phase22",
        title="Route example profiling through command helpers",
        goal="Keep profile-example routed through dataset-oriented io command helpers while cli.py only dispatches arguments.",
        text_checks=(
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="profile_example_command,",
                description="CLI imports the dataset-oriented profile-example command helper",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="return profile_example_command(args)",
                description="CLI delegates profile-example to the command helper",
            ),
            TextCheck(
                path="src/test_data_agent/cli.py",
                text="profile_example_artifacts(",
                description="CLI no longer orchestrates example profiling artifacts directly",
                absent=True,
            ),
        ),
        test_commands=(
            (PYTHON, "-m", "pytest", "tests/test_cli.py", "tests/test_io_commands.py", "tests/test_domain_agnostic_refactor_script.py"),
        ),
    ),
)


def phase_by_id(phase_id: str) -> Phase:
    for phase in PHASES:
        if phase.phase_id == phase_id:
            return phase
    known = ", ".join(phase.phase_id for phase in PHASES)
    raise SystemExit(f"unknown phase {phase_id!r}; expected one of: {known}")


def selected_phases(phase_id: str | None) -> tuple[Phase, ...]:
    if phase_id is None:
        return PHASES
    return (phase_by_id(phase_id),)


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def file_text(path: str) -> str:
    full_path = ROOT / path
    if not full_path.exists():
        return ""
    return full_path.read_text()


def audit_phase(phase: Phase) -> list[str]:
    failures: list[str] = []
    for path in phase.expected_files:
        if not file_exists(path):
            failures.append(f"{phase.phase_id}: missing {path}")
    for check in phase.text_checks:
        content = file_text(check.path)
        contains = check.text in content
        ok = not contains if check.absent else contains
        if not ok:
            expectation = "must not contain" if check.absent else "must contain"
            failures.append(
                f"{phase.phase_id}: {check.path} {expectation} {check.text!r} ({check.description})"
            )
    return failures


def command_plan(args: argparse.Namespace) -> int:
    print(f"Plan: {relative(PLAN_PATH)}")
    print()
    for phase in selected_phases(args.phase):
        print(f"{phase.phase_id}: {phase.title}")
        print(f"  {phase.goal}")
        if phase.expected_files:
            print("  Expected files:")
            for path in phase.expected_files:
                print(f"    - {path}")
        if phase.test_commands:
            print("  Test commands:")
            for command in phase.test_commands:
                print(f"    - {' '.join(command)}")
        print()
    return 0


def command_check(args: argparse.Namespace) -> int:
    failures: list[str] = []
    for phase in selected_phases(args.phase):
        phase_failures = audit_phase(phase)
        if phase_failures:
            print(f"[todo] {phase.phase_id}: {phase.title}")
            for failure in phase_failures:
                print(f"  - {failure}")
        else:
            print(f"[ok]   {phase.phase_id}: {phase.title}")
        failures.extend(phase_failures)

    if failures and args.strict:
        return 1
    return 0


def command_next(args: argparse.Namespace) -> int:
    for phase in PHASES:
        failures = audit_phase(phase)
        if failures:
            print(f"Next incomplete phase: {phase.phase_id} - {phase.title}")
            print(phase.goal)
            print()
            for failure in failures:
                print(f"- {failure}")
            return 0
    print("All tracked phases are complete.")
    return 0


def command_test(args: argparse.Namespace) -> int:
    phase = phase_by_id(args.phase)
    if not phase.test_commands:
        print(f"No test commands configured for {phase.phase_id}.")
        return 0

    for command in phase.test_commands:
        print(f"+ {' '.join(command)}")
        if args.dry_run:
            continue
        completed = subprocess.run(command, cwd=ROOT, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track and verify the DatasetSpec refactoring.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Show the refactoring phases.")
    plan_parser.add_argument("--phase", choices=[phase.phase_id for phase in PHASES])
    plan_parser.set_defaults(func=command_plan)

    check_parser = subparsers.add_parser("check", help="Check phase progress.")
    check_parser.add_argument("--phase", choices=[phase.phase_id for phase in PHASES])
    check_parser.add_argument("--strict", action="store_true", help="Exit non-zero when work remains.")
    check_parser.set_defaults(func=command_check)

    next_parser = subparsers.add_parser("next", help="Show the next incomplete phase.")
    next_parser.set_defaults(func=command_next)

    test_parser = subparsers.add_parser("test", help="Run tests for one phase.")
    test_parser.add_argument("--phase", required=True, choices=[phase.phase_id for phase in PHASES])
    test_parser.add_argument("--dry-run", action="store_true")
    test_parser.set_defaults(func=command_test)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
