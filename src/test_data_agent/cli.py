"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from test_data_agent.adapters import (
    csv_file_to_dataset_profile,
    csv_file_to_dataset_spec,
    generate_legacy_rows,
    legacy_profile_to_generation_spec,
    load_legacy_generation_spec,
    load_profile_or_spec,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io import (
    generate_dataset_artifacts,
    load_dataset_rows,
    load_dataset_spec,
    write_dataset_generation_artifacts,
    write_dataset_profile_artifact,
    write_dataset_review_artifacts,
    write_dataset_spec_artifact,
    write_generation_artifacts,
    write_json_artifact,
    write_dataset_rows,
    write_single_entity_rows,
    write_tabular_rows,
)
from test_data_agent.profiling import profile_example_folder
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path
from test_data_agent.validation import validate_dataset
from test_data_agent.validator import validate_rows_report

if TYPE_CHECKING:
    from test_data_agent.spec import GenerationSpec, OutputFormat


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
        if args.spec is not None and is_dataset_spec_path(args.spec):
            return generate_dataset_command(args)
        warn_legacy_path("generate")
        spec = build_generation_spec(args)
        rows = generate_legacy_rows(spec)
        business_report = apply_business_rules_from_args({spec.table.name: rows}, args, spec.seed)
        report = validate_rows_report(rows, spec)
        write_tabular_rows(rows, spec, args.output)
        write_generation_artifacts(spec, report, args.output, business_report=business_report)
        if should_fail_generation(report, business_report, args.mode):
            for error in report.errors:
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
        profile = DatasetProfile.model_validate_json(args.profile.read_text())
        spec = infer_dataset_spec(profile, count=args.count)
        write_dataset_spec_artifact(spec, args.output)
        return 0

    if args.command == "profile-csv":
        profile = csv_file_to_dataset_profile(args.input, table_name=args.table)
        write_dataset_profile_artifact(profile, args.output)
        return 0

    if args.command == "generate-from-csv":
        profile = csv_file_to_dataset_profile(args.input, table_name=args.table)
        spec = csv_file_to_dataset_spec(args.input, table_name=args.table, count=args.count, seed=args.seed)
        spec.generation_settings.seed = args.seed
        spec.generation_settings.output_format = CoreOutputFormat(args.output_format)
        apply_dataset_mode_options(spec, args.mode, args.invalid_ratio)
        rows_by_entity = generate_dataset(spec, seed=args.seed)
        business_report = apply_business_rules_from_args(rows_by_entity, args, args.seed)
        report = validate_dataset(rows_by_entity, spec)
        if args.output is None:
            raise SystemExit("CSV generation requires --output")
        write_single_entity_rows(rows_by_entity, CoreOutputFormat(args.output_format), args.output)
        write_dataset_generation_artifacts(profile, spec, report, args.output, business_report=business_report)
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
        warn_legacy_path("validate")
        spec = load_spec(args.spec)
        rows = json.loads(args.rows.read_text())
        report = validate_rows_report(rows, spec)
        print(report.model_dump_json(indent=2))
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
        rows_by_entity = generate_dataset(spec, seed=args.seed)
        output_format = CoreOutputFormat(args.output_format)
        write_dataset_rows(rows_by_entity, output_format, args.output)
        report = validate_dataset(rows_by_entity, spec)
        write_dataset_review_artifacts(profile, spec, report, args.output)
        return 0 if report.valid else 1

    return 2


def load_spec(path: Path) -> GenerationSpec:
    return load_legacy_generation_spec(path)


def warn_legacy_path(command: str) -> None:
    print(
        f"warning: '{command}' is using deprecated GenerationSpec compatibility; prefer DatasetSpec inputs",
        file=sys.stderr,
    )


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


def build_generation_spec(args: argparse.Namespace) -> GenerationSpec:
    if args.profile is not None:
        if args.spec is not None:
            raise SystemExit("generate accepts either a spec path or --profile, not both")
        if args.count is None:
            raise SystemExit("--count is required with --profile")
        if args.seed is None:
            raise SystemExit("--seed is required with --profile")
        profile = json.loads(args.profile.read_text())
        spec = legacy_profile_to_generation_spec(
            profile,
            count=args.count,
            seed=args.seed,
        )
    else:
        if args.spec is None:
            raise SystemExit("generate requires a spec path or --profile")
        spec = load_spec(args.spec)
        if args.count is not None:
            spec.table.row_count = args.count
        if args.seed is not None:
            spec.seed = args.seed

    if args.output_format is not None:
        spec.output_format = CoreOutputFormat(args.output_format)
    apply_mode_options(spec, args.mode, args.invalid_ratio)
    return spec


def apply_mode_options(spec: GenerationSpec, mode: str, invalid_ratio: float) -> None:
    if mode in {"mixed", "negative"}:
        if not 0.0 <= invalid_ratio <= 1.0:
            raise SystemExit("--invalid-ratio must be between 0 and 1")
        for column in spec.table.columns:
            column.invalid_ratio = 1.0 if mode == "negative" else invalid_ratio
    elif invalid_ratio:
        raise SystemExit("--invalid-ratio requires --mode mixed or --mode negative")


def apply_dataset_mode_options(spec: DatasetSpec, mode: str, invalid_ratio: float) -> None:
    if mode in {"mixed", "negative"}:
        if not 0.0 <= invalid_ratio <= 1.0:
            raise SystemExit("--invalid-ratio must be between 0 and 1")
        spec.generation_settings.mode = CoreGenerationMode(mode)
        spec.generation_settings.invalid_ratio = invalid_ratio
    elif invalid_ratio:
        raise SystemExit("--invalid-ratio requires --mode mixed or --mode negative")
    else:
        spec.generation_settings.mode = CoreGenerationMode(mode)


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
