"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.compat.legacy_workflows import (
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.io import (
    generate_dataset_from_example_artifacts,
    generate_dataset_from_example_command,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    generate_dataset_from_spec_path,
    generate_dataset_command,
    generate_dataset_from_profile_command,
    is_dataset_spec_path,
    infer_dataset_spec_artifact,
    profile_example_command,
    profile_example_artifacts,
    should_fail_generation,
    validate_dataset_artifacts,
    write_generation_errors,
    write_csv_profile_artifact,
)
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="test-data-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("spec", nargs="?", type=Path)
    generate_parser.add_argument("--profile", type=Path)
    generate_parser.add_argument("--count", type=int)
    generate_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid")
    generate_parser.add_argument("--invalid-ratio", type=float, default=0.0)
    generate_parser.add_argument("--seed", type=int)
    generate_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], dest="output_format")
    generate_parser.add_argument("--output", "-o", type=Path)
    generate_parser.add_argument("--business-rules", type=Path)

    profile_example_parser = subparsers.add_parser("profile-example")
    profile_example_parser.add_argument("input_folder", type=Path)
    profile_example_parser.add_argument("--output", "-o", type=Path, required=True)
    profile_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"))
    profile_example_parser.add_argument("--no-cache", action="store_true")
    profile_example_parser.add_argument("--rule-sample-rows", type=int, default=50_000)

    infer_spec_parser = subparsers.add_parser("infer-spec")
    infer_spec_parser.add_argument("profile", type=Path)
    infer_spec_parser.add_argument("--output", "-o", type=Path, required=True)
    infer_spec_parser.add_argument("--count", type=int)

    profile_csv_parser = subparsers.add_parser("profile-csv")
    profile_csv_parser.add_argument("input", type=Path)
    profile_csv_parser.add_argument("--table", type=str)
    profile_csv_parser.add_argument("--output", "-o", type=Path, required=True)

    generate_csv_parser = subparsers.add_parser("generate-from-csv")
    generate_csv_parser.add_argument("input", type=Path)
    generate_csv_parser.add_argument("--count", type=int, required=True)
    generate_csv_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid")
    generate_csv_parser.add_argument("--invalid-ratio", type=float, default=0.0)
    generate_csv_parser.add_argument("--seed", type=int, required=True)
    generate_csv_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format")
    generate_csv_parser.add_argument("--output", "-o", type=Path, required=True)
    generate_csv_parser.add_argument("--table", type=str)
    generate_csv_parser.add_argument("--business-rules", type=Path)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("spec", type=Path)
    validate_parser.add_argument("rows", type=Path)
    validate_parser.add_argument("--output", "-o", type=Path)

    generate_example_parser = subparsers.add_parser("generate-from-example")
    generate_example_parser.add_argument("input_folder", type=Path)
    generate_example_parser.add_argument("--output", "-o", type=Path, required=True)
    generate_example_parser.add_argument("--seed", type=int, required=True)
    generate_example_parser.add_argument("--count", type=int)
    generate_example_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format")
    generate_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"))
    generate_example_parser.add_argument("--no-cache", action="store_true")
    generate_example_parser.add_argument("--rule-sample-rows", type=int, default=50_000)

    args = parser.parse_args(argv)

    if args.command == "generate":
        if args.profile is not None:
            return generate_dataset_from_profile_command(
                args,
                business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                    rows_by_entity,
                    args,
                    seed,
                ),
            )
        if args.spec is not None and is_dataset_spec_path(args.spec):
            return generate_dataset_command(args)
        legacy_result, business_report = generate_legacy_spec_artifacts(
            args.spec,
            row_count=args.count,
            seed=args.seed,
            output_format=None if args.output_format is None else CoreOutputFormat(args.output_format),
            output_path=args.output,
            mode=args.mode,
            invalid_ratio=args.invalid_ratio,
            business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
            ),
        )
        if should_fail_generation(legacy_result.report, business_report, args.mode):
            for error in legacy_result.report.errors:
                print(error, file=sys.stderr)
            if business_report is not None and not business_report.valid:
                print("business validation failed", file=sys.stderr)
            return 1
        return 0

    if args.command == "profile-example":
        return profile_example_command(args)

    if args.command == "infer-spec":
        loaded = load_profile_or_spec(args.profile)
        if isinstance(loaded, DatasetSpec):
            raise SystemExit("infer-spec expects a dataset profile, not a dataset spec")
        infer_dataset_spec_artifact(loaded, output_path=args.output, count=args.count)
        return 0

    if args.command == "profile-csv":
        write_csv_profile_artifact(args.input, output_path=args.output, table_name=args.table)
        return 0

    if args.command == "generate-from-csv":
        report, business_report = generate_dataset_from_csv_artifacts(
            args.input,
            count=args.count,
            seed=args.seed,
            output_path=args.output,
            output_format=CoreOutputFormat(args.output_format),
            table_name=args.table,
            mode=args.mode,
            invalid_ratio=args.invalid_ratio,
            business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
            ),
        )
        if should_fail_generation(report, business_report, args.mode):
            write_generation_errors(report, business_report)
            return 1
        return 0

    if args.command == "validate":
        if is_dataset_spec_path(args.spec) or args.rows.is_dir():
            report = validate_dataset_artifacts(
                args.spec,
                args.rows,
                output_path=args.output,
            )
            text = report.model_dump_json(indent=2)
            if args.output is None:
                print(text)
            return 0 if report.valid else 1
        report = validate_legacy_spec_artifacts(
            args.spec,
            args.rows,
            output_path=args.output,
        )
        if not report.valid:
            return 1
        return 0

    if args.command == "generate-from-example":
        return generate_dataset_from_example_command(args)

    return 2


def apply_business_rules_from_args(rows_by_table: dict[str, list[dict[str, Any]]], args: argparse.Namespace, seed: int) -> Any | None:
    return apply_and_validate_business_rules_from_path(
        rows_by_table,
        getattr(args, "business_rules", None),
        seed=seed,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
    )


if __name__ == "__main__":
    raise SystemExit(main())
