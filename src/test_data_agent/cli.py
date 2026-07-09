"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from test_data_agent.compat.commands import generate_legacy_command, validate_legacy_command
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.io import (
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    generate_dataset_from_spec_path,
)
from test_data_agent.io import (
    generate_dataset_from_example_artifacts,
    generate_dataset_from_example_command,
    generate_dataset_from_profile_command,
    generate_dataset_command,
    infer_dataset_spec_command,
    is_dataset_spec_path,
    profile_csv_command,
    profile_example_artifacts,
    should_fail_generation,
    validate_dataset_artifacts,
    write_generation_errors,
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
        return generate_legacy_command(
            args,
            business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
            ),
        )

    if args.command == "profile-example":
        profile_example_artifacts(
            args.input_folder,
            output_path=args.output,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
            rule_sample_rows=args.rule_sample_rows,
        )
        return 0

    if args.command == "infer-spec":
        return infer_dataset_spec_command(args)

    if args.command == "profile-csv":
        return profile_csv_command(args)

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
        return validate_legacy_command(args)

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
