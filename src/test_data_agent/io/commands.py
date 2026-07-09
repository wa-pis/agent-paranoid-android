"""Command helpers for DatasetSpec-oriented CLI flows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_json_artifact
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    generate_dataset_artifacts,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    generate_dataset_review_artifacts,
    infer_dataset_spec_artifact,
    write_csv_profile_artifact,
)
from test_data_agent.profiling import profile_example_folder
from test_data_agent.validation import DatasetValidationReport, validate_dataset

BusinessRulesApplier = Callable[[dict[str, list[dict[str, Any]]], int], Any | None]


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


def generate_dataset_from_spec_path(
    spec_path: Path,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
) -> int:
    spec = load_dataset_spec(spec_path)
    return generate_dataset_artifacts(
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
    )


def generate_dataset_command(args: argparse.Namespace) -> int:
    if args.output is None:
        raise SystemExit("dataset generation requires --output folder")
    output_format = None if args.output_format is None else OutputFormat(args.output_format)
    return generate_dataset_from_spec_path(
        args.spec,
        output_folder=args.output,
        output_format=output_format,
        seed=args.seed,
        count=args.count,
    )


def generate_dataset_from_profile_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
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
            output_format=None if args.output_format is None else OutputFormat(args.output_format),
            mode=args.mode,
            invalid_ratio=args.invalid_ratio,
            business_rules_applier=business_rules_applier,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if should_fail_generation(report, business_report, args.mode):
        write_generation_errors(report, business_report)
        return 1
    return 0


def profile_example_command(args: argparse.Namespace) -> int:
    profile_example_artifacts(
        args.input_folder,
        output_path=args.output,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
        rule_sample_rows=args.rule_sample_rows,
    )
    return 0


def validate_dataset_artifacts(
    spec_path: Path,
    rows_path: Path,
    *,
    output_path: Path | None = None,
) -> DatasetValidationReport:
    spec = load_dataset_spec(spec_path)
    rows_by_entity = load_dataset_rows(rows_path)
    report = validate_dataset(rows_by_entity, spec)
    if output_path is not None:
        write_json_artifact(report, output_path)
    return report


def infer_dataset_spec_command(args: argparse.Namespace) -> int:
    loaded = load_profile_or_spec(args.profile)
    if isinstance(loaded, DatasetSpec):
        raise SystemExit("infer-spec expects a dataset profile, not a dataset spec")
    infer_dataset_spec_artifact(loaded, output_path=args.output, count=args.count)
    return 0


def profile_csv_command(args: argparse.Namespace) -> int:
    write_csv_profile_artifact(args.input, output_path=args.output, table_name=args.table)
    return 0


def generate_dataset_from_csv_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    report, business_report = generate_dataset_from_csv_artifacts(
        args.input,
        count=args.count,
        seed=args.seed,
        output_path=args.output,
        output_format=OutputFormat(args.output_format),
        table_name=args.table,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
        business_rules_applier=business_rules_applier,
    )
    if should_fail_generation(report, business_report, args.mode):
        write_generation_errors(report, business_report)
        return 1
    return 0


def profile_example_artifacts(
    input_folder: Path,
    *,
    output_path: Path,
    cache_dir: Path,
    use_cache: bool = True,
    rule_sample_rows: int = 50_000,
):
    profile = profile_example_folder(
        input_folder,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )
    write_json_artifact(profile, output_path)
    return profile


def generate_dataset_from_example_artifacts(
    input_folder: Path,
    *,
    output_folder: Path,
    seed: int,
    count: int | None,
    output_format: OutputFormat,
    cache_dir: Path,
    use_cache: bool = True,
    rule_sample_rows: int = 50_000,
) -> int:
    profile = profile_example_folder(
        input_folder,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )
    spec = infer_dataset_spec_artifact(
        profile,
        output_path=output_folder / "dataset_spec.yaml",
        count=count,
    )
    return generate_dataset_review_artifacts(
        profile,
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
    )


def generate_dataset_from_example_command(args: argparse.Namespace) -> int:
    return generate_dataset_from_example_artifacts(
        args.input_folder,
        output_folder=args.output,
        seed=args.seed,
        count=args.count,
        output_format=OutputFormat(args.output_format),
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
        rule_sample_rows=args.rule_sample_rows,
    )


def write_generation_errors(schema_report: Any, business_report: Any | None) -> None:
    for section in schema_report.sections:
        for error in section.errors:
            print(error, file=sys.stderr)
    if business_report is not None and not business_report.valid:
        print("business validation failed", file=sys.stderr)


def should_fail_generation(schema_report: Any, business_report: Any | None, mode: str) -> bool:
    if mode in {"mixed", "negative"}:
        return False
    if not schema_report.valid:
        return True
    return business_report is not None and not business_report.valid
