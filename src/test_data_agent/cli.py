"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io import (
    generate_dataset_artifacts,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    generate_dataset_review_artifacts,
    infer_dataset_spec_artifact,
    load_dataset_rows,
    load_dataset_spec,
    write_dataset_profile_artifact,
    write_csv_profile_artifact,
    write_json_artifact,
)
from test_data_agent.io.legacy_workflows import (
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)
from test_data_agent.profiling import profile_example_folder
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path
from test_data_agent.validation import validate_dataset


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
            return generate_dataset_from_profile_command(args)
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
        profile = profile_example_folder(
            args.input_folder,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
            rule_sample_rows=args.rule_sample_rows,
        )
        write_dataset_profile_artifact(profile, args.output)
        return 0

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
            for section in report.sections:
                for error in section.errors:
                    print(error, file=sys.stderr)
            if business_report is not None and not business_report.valid:
                print("business validation failed", file=sys.stderr)
            return 1
        return 0

    if args.command == "validate":
        if is_dataset_spec_path(args.spec) or args.rows.is_dir():
            spec = load_dataset_spec(args.spec)
            rows_by_entity = load_dataset_rows(args.rows)
            report = validate_dataset(rows_by_entity, spec)
            text = report.model_dump_json(indent=2)
            if args.output is not None:
                write_json_artifact(report, args.output)
            else:
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
        profile = profile_example_folder(
            args.input_folder,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
            rule_sample_rows=args.rule_sample_rows,
        )
        spec = infer_dataset_spec(profile, count=args.count)
        output_format = CoreOutputFormat(args.output_format)
        return generate_dataset_review_artifacts(
            profile,
            spec,
            output_folder=args.output,
            output_format=output_format,
            seed=args.seed,
        )

    return 2


def is_dataset_spec_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return True
    if suffix != ".json":
        return False
    try:
        return isinstance(load_profile_or_spec(path), DatasetSpec)
    except Exception:
        return False


def generate_dataset_command(args: argparse.Namespace) -> int:
    spec = load_dataset_spec(args.spec)
    if args.output is None:
        raise SystemExit("dataset generation requires --output folder")
    output_format = None if args.output_format is None else CoreOutputFormat(args.output_format)
    return generate_dataset_artifacts(
        spec,
        output_folder=args.output,
        output_format=output_format,
        seed=args.seed,
        count=args.count,
    )


def generate_dataset_from_profile_command(args: argparse.Namespace) -> int:
    if args.spec is not None:
        raise SystemExit("generate accepts either a spec path or --profile, not both")
    if args.profile is None:
        raise SystemExit("generate requires a spec path or --profile")
    if args.count is None:
        raise SystemExit("--count is required with --profile")
    if args.seed is None:
        raise SystemExit("--seed is required with --profile")

    loaded = load_profile_or_spec(args.profile)
    if isinstance(loaded, DatasetSpec):
        raise SystemExit("--profile expects a dataset profile, not a dataset spec")
    profile = loaded

    try:
        report, business_report = generate_dataset_from_profile_artifacts(
            profile,
            count=args.count,
            seed=args.seed,
            output_path=args.output,
            output_format=None if args.output_format is None else CoreOutputFormat(args.output_format),
            mode=args.mode,
            invalid_ratio=args.invalid_ratio,
            business_rules_applier=lambda rows_by_entity, seed: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
            ),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if should_fail_generation(report, business_report, args.mode):
        for section in report.sections:
            for error in section.errors:
                print(error, file=sys.stderr)
        if business_report is not None and not business_report.valid:
            print("business validation failed", file=sys.stderr)
        return 1
    return 0


def apply_business_rules_from_args(rows_by_table: dict[str, list[dict[str, Any]]], args: argparse.Namespace, seed: int) -> Any | None:
    return apply_and_validate_business_rules_from_path(
        rows_by_table,
        getattr(args, "business_rules", None),
        seed=seed,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
    )


def should_fail_generation(schema_report: Any, business_report: Any | None, mode: str) -> bool:
    if mode in {"mixed", "negative"}:
        return False
    if not schema_report.valid:
        return True
    return business_report is not None and not business_report.valid


if __name__ == "__main__":
    raise SystemExit(main())
