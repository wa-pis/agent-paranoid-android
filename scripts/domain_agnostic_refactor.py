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
                text="from test_data_agent.compat import",
                description="CLI imports deprecated workflows from compat boundary",
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
