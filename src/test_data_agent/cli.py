"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from test_data_agent.agent import AgentRequest, AgentResult, AgentSourceType, approve_agent_workspace, plan_agent_request
from test_data_agent.compat.commands import generate_legacy_command, validate_legacy_command
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.generation.constraint_solver import default_value_for_field
from test_data_agent.io import (
    generate_dataset_from_csv_command,
    generate_dataset_from_example_artifacts,
    generate_dataset_from_example_command,
    generate_dataset_from_profile_command,
    generate_dataset_command,
    infer_dataset_spec_command,
    is_dataset_spec_path,
    profile_csv_command,
    profile_example_command,
    validate_dataset_artifacts,
)
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="test-data-agent",
        description=(
            "Agent Paranoid Android: safe deterministic synthetic data generation "
            "from CSV files, CSV folders, safe profiles, or dataset specs."
        ),
        epilog=(
            "Start here:\n"
            "  CSV file:    test-data-agent generate-from-csv data/customers.csv --count 100 --seed 123 --format csv --output out/customers.csv\n"
            "  CSV folder:  test-data-agent generate-from-example data/example_dataset --count 100 --seed 123 --format csv --output out/generated\n"
            "  AI agent:    test-data-agent agent-plan data/example_dataset --source-type csv-folder --workspace out/agent\n"
            "  Self-check:   test-data-agent doctor\n"
            "  Validate:    test-data-agent validate out/generated/dataset_spec.yaml out/generated\n\n"
            "The generated rows are synthetic. Review generation_manifest.json after generation for the seed, row counts, and safety flags."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a dataset from a DatasetSpec, or from a safe profile with --profile.",
        description="Generate synthetic rows from a DatasetSpec file or safe profile metadata.",
    )
    generate_parser.add_argument("spec", nargs="?", type=Path)
    generate_parser.add_argument("--profile", type=Path, help="Safe profile JSON to generate from instead of a spec file.")
    generate_parser.add_argument("--count", type=positive_int, help="Override generated row count per entity.")
    generate_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid", help="Generation mode: valid rows by default, or controlled invalid/edge data.")
    generate_parser.add_argument("--invalid-ratio", type=ratio, default=0.0, help="Share of invalid values for mixed/negative modes, between 0 and 1.")
    generate_parser.add_argument("--seed", type=non_negative_int, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], dest="output_format", help="Output format for generated rows.")
    generate_parser.add_argument("--output", "-o", type=Path, help="Output folder for DatasetSpec generation, or output file for --profile.")
    generate_parser.add_argument("--business-rules", type=Path, help="Optional YAML/JSON business rules to enforce and validate.")
    generate_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing single-file output.")

    profile_example_parser = subparsers.add_parser(
        "profile-example",
        aliases=["profile-csv-folder"],
        help="Create a safe profile from a folder of related CSV files.",
        description="Profile a CSV folder without writing source rows or raw PII to the profile.",
    )
    profile_example_parser.add_argument("input_folder", type=Path, help="Folder containing one CSV file per table.")
    profile_example_parser.add_argument("--output", "-o", type=Path, required=True, help="Profile JSON to write.")
    profile_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"), help="Safe profile cache directory.")
    profile_example_parser.add_argument("--no-cache", action="store_true", help="Force a fresh profile instead of reusing the cache.")
    profile_example_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000, help="Rows sampled for relationship and rule mining.")
    profile_example_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing profile JSON.")

    infer_spec_parser = subparsers.add_parser(
        "infer-spec",
        help="Infer a reusable DatasetSpec YAML from a safe profile.",
        description="Turn a safe profile JSON into a DatasetSpec YAML recipe for generation.",
    )
    infer_spec_parser.add_argument("profile", type=Path, help="Safe profile JSON.")
    infer_spec_parser.add_argument("--output", "-o", type=Path, required=True, help="DatasetSpec YAML/JSON to write.")
    infer_spec_parser.add_argument("--count", type=positive_int, help="Override row count per entity in the inferred spec.")
    infer_spec_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing spec file.")

    profile_csv_parser = subparsers.add_parser(
        "profile-csv",
        help="Create a safe profile from one CSV file.",
        description="Profile one CSV file into safe metadata: schema, distributions, ranges, and masked sensitive patterns.",
    )
    profile_csv_parser.add_argument("input", type=Path, help="Source CSV file. Source rows are not copied to the profile.")
    profile_csv_parser.add_argument("--table", type=str, help="Table/entity name to use in the profile.")
    profile_csv_parser.add_argument("--output", "-o", type=Path, required=True, help="Profile JSON to write.")
    profile_csv_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing profile JSON.")

    generate_csv_parser = subparsers.add_parser(
        "generate-from-csv",
        help="Generate a synthetic single-table dataset directly from one CSV file.",
        description="Profile one CSV file, infer a generation spec, generate synthetic rows, and validate the result.",
        epilog=(
            "Example:\n"
            "  test-data-agent generate-from-csv tests/fixtures/customers.csv "
            "--count 25 --seed 12345 --format csv --output out/customers.csv\n\n"
            "Writes csv_profile.json, generation_spec.json, validation_report.json, "
            "and generation_manifest.json next to the output file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_csv_parser.add_argument("input", type=Path, help="Source CSV file used only for safe metadata.")
    generate_csv_parser.add_argument("--count", type=positive_int, required=True, help="Number of synthetic rows to generate.")
    generate_csv_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid", help="Generation mode: valid rows by default, or controlled invalid/edge data.")
    generate_csv_parser.add_argument("--invalid-ratio", type=ratio, default=0.0, help="Share of invalid values for mixed/negative modes, between 0 and 1.")
    generate_csv_parser.add_argument("--seed", type=non_negative_int, required=True, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_csv_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format", help="Output format for generated rows.")
    generate_csv_parser.add_argument("--output", "-o", type=Path, required=True, help="Generated output file.")
    generate_csv_parser.add_argument("--table", type=str, help="Table/entity name to use for the generated dataset.")
    generate_csv_parser.add_argument("--business-rules", type=Path, help="Optional YAML/JSON business rules to enforce and validate.")
    generate_csv_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing generated file.")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate generated rows against a DatasetSpec.",
        description="Validate generated files and optionally write a validation_report.json.",
    )
    validate_parser.add_argument("spec", type=Path, help="DatasetSpec YAML/JSON.")
    validate_parser.add_argument("rows", type=Path, help="Generated output folder or legacy rows file.")
    validate_parser.add_argument("--output", "-o", type=Path, help="Validation report JSON to write.")
    validate_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing validation report.")

    generate_example_parser = subparsers.add_parser(
        "generate-from-example",
        aliases=["generate-from-csv-folder"],
        help="Generate a related multi-table dataset from a folder of CSV examples.",
        description="Profile a CSV folder, infer a DatasetSpec, generate synthetic related tables, and validate them.",
        epilog=(
            "Example:\n"
            "  test-data-agent generate-from-example tests/fixtures/example_dataset "
            "--count 25 --seed 12345 --format csv --output out/example_dataset\n\n"
            "Writes profile.json, dataset_spec.yaml, validation_report.json, "
            "generation_manifest.json, and one synthetic data file per entity."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_example_parser.add_argument("input_folder", type=Path, help="Folder containing one CSV file per table.")
    generate_example_parser.add_argument("--output", "-o", type=Path, required=True, help="Output folder for generated tables and review artifacts.")
    generate_example_parser.add_argument("--seed", type=non_negative_int, required=True, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_example_parser.add_argument("--count", type=positive_int, help="Override generated row count per entity.")
    generate_example_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format", help="Output format for generated rows.")
    generate_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"), help="Safe profile cache directory.")
    generate_example_parser.add_argument("--no-cache", action="store_true", help="Force a fresh profile instead of reusing the cache.")
    generate_example_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000, help="Rows sampled for relationship and rule mining.")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run local environment and fixture smoke checks.",
        description="Check Python version, runtime dependencies, fixture data, and a small synthetic generation smoke test.",
    )
    doctor_parser.add_argument("--skip-smoke", action="store_true", help="Only check Python and importable dependencies.")

    agent_plan_parser = subparsers.add_parser(
        "agent-plan",
        help="Plan a safe agent workflow and stop before generation.",
        description="Profile input data, infer a reviewable DatasetSpec, and require approval before generation.",
        epilog=(
            "Example:\n"
            "  test-data-agent agent-plan tests/fixtures/example_dataset "
            "--source-type csv-folder --workspace out/agent --count 25 --seed 12345 --format csv\n"
            "  test-data-agent agent-approve out/agent"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_plan_parser.add_argument("source", type=Path, help="CSV file, CSV folder, or safe profile JSON.")
    agent_plan_parser.add_argument("--source-type", choices=["csv", "csv-folder", "profile"], required=True)
    agent_plan_parser.add_argument("--workspace", type=Path, required=True, help="Empty folder for agent artifacts.")
    agent_plan_parser.add_argument("--count", type=positive_int, default=100, help="Synthetic row count per entity.")
    agent_plan_parser.add_argument("--seed", type=non_negative_int, default=12345, help="Deterministic generation seed.")
    agent_plan_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], default="csv", dest="output_format")
    agent_plan_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid")
    agent_plan_parser.add_argument("--invalid-ratio", type=ratio, default=0.0)
    agent_plan_parser.add_argument("--table", type=str, help="Table/entity name for single CSV sources.")
    agent_plan_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000)
    agent_plan_parser.add_argument("--use-cache", action="store_true", help="Use a safe profile cache inside the agent workspace.")

    agent_approve_parser = subparsers.add_parser(
        "agent-approve",
        help="Approve a planned agent workflow and generate synthetic data.",
        description="Load a prepared agent workspace, use the reviewed DatasetSpec, generate data, and validate it.",
    )
    agent_approve_parser.add_argument("workspace", type=Path, help="Workspace created by agent-plan.")

    args = parser.parse_args(argv)

    try:
        return run_command(args)
    except SystemExit:
        raise
    except FileNotFoundError as exc:
        print(f"Error: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except (IsADirectoryError, NotADirectoryError, PermissionError) as exc:
        print(f"Error: {exc.strerror}: {exc.filename}", file=sys.stderr)
        return 2
    except (ValidationError, ValueError) as exc:
        print(f"Error: {friendly_error(exc)}", file=sys.stderr)
        return 2


def run_command(args: argparse.Namespace) -> int:
    if args.command == "generate":
        if args.profile is not None:
            return generate_dataset_from_profile_command(
                args,
                business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                    rows_by_entity,
                    args,
                    seed,
                    spec,
                ),
            )
        if args.spec is not None and is_dataset_spec_path(args.spec):
            return generate_dataset_command(
                args,
                business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                    rows_by_entity,
                    args,
                    seed,
                    spec,
                ),
            )
        return generate_legacy_command(
            args,
            business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
            ),
        )

    if args.command in {"profile-example", "profile-csv-folder"}:
        return profile_example_command(args)

    if args.command == "infer-spec":
        return infer_dataset_spec_command(args)

    if args.command == "profile-csv":
        return profile_csv_command(args)

    if args.command == "generate-from-csv":
        return generate_dataset_from_csv_command(
            args,
            business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
                spec,
            ),
        )

    if args.command == "validate":
        if is_dataset_spec_path(args.spec) or args.rows.is_dir():
            report = validate_dataset_artifacts(
                args.spec,
                args.rows,
                output_path=args.output,
                overwrite=args.overwrite,
            )
            write_validation_summary(report, args.output)
            text = report.model_dump_json(indent=2)
            if args.output is None:
                print(text)
            return 0 if report.valid else 1
        return validate_legacy_command(args)

    if args.command in {"generate-from-example", "generate-from-csv-folder"}:
        return generate_dataset_from_example_command(args)

    if args.command == "doctor":
        return run_doctor(skip_smoke=args.skip_smoke)

    if args.command == "agent-plan":
        result = plan_agent_request(agent_request_from_args(args))
        write_agent_result_summary(result)
        return 0

    if args.command == "agent-approve":
        result = approve_agent_workspace(args.workspace)
        write_agent_result_summary(result)
        return 0 if result.summary.get("validation_valid", False) else 1

    return 2


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def ratio(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def friendly_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ()))
        message = first.get("msg", str(exc))
        return f"{location}: {message}" if location else message
    return str(exc)


def write_validation_summary(report: Any, output: Path | None) -> None:
    failed = sum(section.failed for section in report.sections)
    passed = sum(section.passed for section in report.sections)
    status = "passed" if report.valid else "failed"
    destination = f" Report: {output}" if output is not None else ""
    print(f"Validation {status}: {passed} checks passed, {failed} failed.{destination}", file=sys.stderr)


def run_doctor(*, skip_smoke: bool = False) -> int:
    checks: list[str] = []
    failures: list[str] = []

    if sys.version_info >= (3, 11):
        checks.append(f"python: ok ({sys.version_info.major}.{sys.version_info.minor})")
    else:
        failures.append("python: Python 3.11 or newer is required")

    for module_name in ("faker", "pydantic", "pyarrow", "sqlglot", "trino", "yaml"):
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            failures.append(f"dependency {module_name}: missing ({exc})")
        else:
            checks.append(f"dependency {module_name}: ok")

    fixture = find_example_fixture()
    if fixture.is_dir():
        checks.append(f"fixture: ok ({fixture})")
    else:
        failures.append(f"fixture: missing {fixture}")

    if not skip_smoke and not failures:
        with tempfile.TemporaryDirectory(prefix="test-data-agent-doctor-") as tmp:
            output = Path(tmp) / "generated"
            cache_dir = Path(tmp) / "cache"
            generate_dataset_from_example_artifacts(
                fixture,
                output_folder=output,
                seed=12345,
                count=3,
                output_format=CoreOutputFormat.CSV,
                cache_dir=cache_dir,
                use_cache=False,
            )
            manifest = json.loads((output / "generation_manifest.json").read_text())
            if (
                manifest.get("synthetic") is True
                and manifest.get("source_rows_copied") is False
                and manifest.get("validation_valid") is True
            ):
                checks.append("quickstart smoke: ok")
            else:
                failures.append("quickstart smoke: manifest safety flags are not valid")

    for check in checks:
        print(check, file=sys.stderr)
    for failure in failures:
        print(f"doctor failed: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("doctor passed", file=sys.stderr)
    return 0


def find_example_fixture() -> Path:
    for root in (Path.cwd(), Path(__file__).resolve().parents[2]):
        fixture = root / "tests" / "fixtures" / "example_dataset"
        if fixture.is_dir():
            return fixture
    return Path.cwd() / "tests" / "fixtures" / "example_dataset"


def agent_request_from_args(args: argparse.Namespace) -> AgentRequest:
    return AgentRequest(
        source_type=AgentSourceType(args.source_type.replace("-", "_")),
        source_path=args.source,
        workspace=args.workspace,
        count=args.count,
        seed=args.seed,
        output_format=CoreOutputFormat(args.output_format),
        mode=CoreGenerationMode(args.mode),
        invalid_ratio=args.invalid_ratio,
        table_name=args.table,
        rule_sample_rows=args.rule_sample_rows,
        use_cache=args.use_cache,
    )


def write_agent_result_summary(result: AgentResult) -> None:
    if result.phase.value == "awaiting_approval":
        print(
            "Agent plan ready: "
            f"{result.artifacts.workspace} | spec: {result.artifacts.dataset_spec_path} | "
            "approve with: test-data-agent agent-approve "
            f"{result.artifacts.workspace}",
            file=sys.stderr,
        )
        return
    row_counts = result.summary.get("row_counts", {})
    rows_text = ", ".join(f"{name}={count}" for name, count in row_counts.items()) or "no rows"
    validation = "passed" if result.summary.get("validation_valid") else "failed"
    print(
        "Agent generation completed: "
        f"{result.artifacts.generated_folder} | rows: {rows_text} | "
        f"seed: {result.summary.get('seed')} | validation: {validation} | "
        "source rows copied: no",
        file=sys.stderr,
    )


def apply_business_rules_from_args(
    rows_by_table: dict[str, list[dict[str, Any]]],
    args: argparse.Namespace,
    seed: int,
    spec: DatasetSpec | None = None,
) -> Any | None:
    field_defaults = None
    if spec is not None:
        field_defaults = {
            entity.name: {
                field.name: default_value_for_field(field)
                for field in entity.fields
            }
            for entity in spec.entities
        }
    return apply_and_validate_business_rules_from_path(
        rows_by_table,
        getattr(args, "business_rules", None),
        seed=seed,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
        field_defaults=field_defaults,
        spec=spec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
