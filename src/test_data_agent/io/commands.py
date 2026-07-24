"""Command helpers for DatasetSpec-oriented CLI flows."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io.artifacts import write_json_artifact
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    ensure_empty_output_folder,
    ensure_folders_distinct,
    ensure_paths_distinct,
    require_output_suffix,
    commit_temp_output_folder,
    generate_dataset_artifacts,
    generate_dataset_from_csv_artifacts,
    generate_dataset_from_profile_artifacts,
    generate_dataset_review_artifacts,
    infer_dataset_spec_artifact,
    make_temp_output_folder,
    write_csv_profile_artifact,
)
from test_data_agent.profiling import profile_example_folder
from test_data_agent.safety import assert_profile_safe
from test_data_agent.validation import DatasetValidationReport, validate_dataset

BusinessRulesApplier = Callable[..., Any | None]


def generate_dataset_from_spec_path(
    spec_path: Path,
    *,
    output_folder: Path,
    output_format: OutputFormat | None = None,
    seed: int | None = None,
    count: int | None = None,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    spec = load_dataset_spec(spec_path)
    exit_code = generate_dataset_artifacts(
        spec,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
        business_rules_applier=business_rules_applier,
    )
    write_generation_summary(output_folder)
    return exit_code


def generate_dataset_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    if args.output is None:
        raise SystemExit("dataset generation requires --output folder")
    output_format = None if args.output_format is None else OutputFormat(args.output_format)
    return generate_dataset_from_spec_path(
        args.spec,
        output_folder=args.output,
        output_format=output_format,
        seed=args.seed,
        count=args.count,
        business_rules_applier=business_rules_applier,
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
    if args.output is not None:
        ensure_paths_distinct(args.profile, args.output)
        ensure_file_output_available(args.output, overwrite=getattr(args, "overwrite", False))

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
    write_generation_summary(args.output.parent if args.output is not None else Path.cwd())
    return 0


def profile_example_command(args: argparse.Namespace) -> int:
    ensure_file_output_available(args.output, overwrite=getattr(args, "overwrite", False))
    profile_example_artifacts(
        args.input_folder,
        output_path=args.output,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
        rule_sample_rows=args.rule_sample_rows,
    )
    write_profile_summary(args.output)
    return 0


def validate_dataset_artifacts(
    spec_path: Path,
    rows_path: Path,
    *,
    output_path: Path | None = None,
    overwrite: bool = False,
) -> DatasetValidationReport:
    spec = load_dataset_spec(spec_path)
    if not rows_path.is_dir():
        raise ValueError(
            "validate expects a dataset output folder; pass the folder containing generated entity files"
        )
    rows_by_entity = load_dataset_rows(rows_path)
    report = validate_dataset(rows_by_entity, spec)
    if output_path is not None:
        ensure_file_output_available(output_path, overwrite=overwrite)
        write_json_artifact(report, output_path)
    return report


def infer_dataset_spec_command(args: argparse.Namespace) -> int:
    ensure_paths_distinct(args.profile, args.output)
    ensure_file_output_available(args.output, overwrite=getattr(args, "overwrite", False))
    loaded = load_profile_or_spec(args.profile)
    if isinstance(loaded, DatasetSpec):
        raise SystemExit("infer-spec expects a dataset profile, not a dataset spec")
    spec = infer_dataset_spec_artifact(loaded, output_path=args.output, count=args.count)
    print(
        f"Wrote dataset spec: {args.output} ({len(spec.entities)} entities)",
        file=sys.stderr,
    )
    return 0


def profile_csv_command(args: argparse.Namespace) -> int:
    ensure_file_output_available(args.output, overwrite=getattr(args, "overwrite", False))
    write_csv_profile_artifact(args.input, output_path=args.output, table_name=args.table)
    write_profile_summary(args.output)
    return 0


def generate_dataset_from_csv_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    ensure_paths_distinct(args.input, args.output)
    ensure_file_output_available(args.output, overwrite=getattr(args, "overwrite", False))
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
    write_generation_summary(args.output.parent)
    return 0


def profile_example_artifacts(
    input_folder: Path,
    *,
    output_path: Path,
    cache_dir: Path,
    use_cache: bool = True,
    rule_sample_rows: int = 50_000,
):
    require_output_suffix(output_path, {".json"}, "profile output")
    input_folder_resolved = input_folder.resolve(strict=True)
    output_resolved = output_path.resolve(strict=False)
    if output_resolved.parent == input_folder_resolved and output_resolved.suffix.lower() == ".csv":
        raise ValueError("profile output must not overwrite a source CSV")
    profile = profile_example_folder(
        input_folder,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )
    assert_profile_safe(profile)
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
    ensure_folders_distinct(input_folder, output_folder)
    ensure_empty_output_folder(output_folder)
    profile = profile_example_folder(
        input_folder,
        cache_dir=cache_dir,
        use_cache=use_cache,
        rule_sample_rows=rule_sample_rows,
    )
    temp_folder = make_temp_output_folder(output_folder)
    try:
        spec = infer_dataset_spec(profile, count=count)
        result = generate_dataset_review_artifacts(
            profile,
            spec,
            output_folder=temp_folder,
            output_format=output_format,
            seed=seed,
            source_folder=input_folder,
        )
        commit_temp_output_folder(temp_folder, output_folder)
        return result
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise


def generate_dataset_from_example_command(args: argparse.Namespace) -> int:
    exit_code = generate_dataset_from_example_artifacts(
        args.input_folder,
        output_folder=args.output,
        seed=args.seed,
        count=args.count,
        output_format=OutputFormat(args.output_format),
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
        rule_sample_rows=args.rule_sample_rows,
    )
    write_generation_summary(args.output)
    return exit_code


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


def ensure_file_output_available(path: Path, *, overwrite: bool = False) -> None:
    if not path.exists():
        return
    if path.is_dir():
        raise ValueError(f"output path is a directory, expected a file: {path}")
    if not overwrite:
        raise ValueError(f"output already exists: {path}. Use --overwrite to replace it.")


def write_profile_summary(profile_path: Path) -> None:
    try:
        profile = json.loads(profile_path.read_text())
    except (OSError, json.JSONDecodeError):
        print(f"Wrote safe profile: {profile_path}", file=sys.stderr)
        return
    entity_count = len(profile.get("entities", []))
    source_type = profile.get("source_type", "profile")
    print(f"Wrote safe {source_type} profile: {profile_path} ({entity_count} entities)", file=sys.stderr)


def write_generation_summary(artifact_folder: Path) -> None:
    manifest_path = artifact_folder / "generation_manifest.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        print(f"Wrote synthetic dataset artifacts: {artifact_folder}", file=sys.stderr)
        return
    row_counts = manifest.get("row_counts", {})
    rows_text = ", ".join(f"{name}={count}" for name, count in row_counts.items()) or "no rows"
    validation = "passed" if manifest.get("validation_valid") else "failed"
    copied = "yes" if manifest.get("source_rows_copied") else "no"
    print(
        "Generated synthetic dataset: "
        f"{artifact_folder} | rows: {rows_text} | seed: {manifest.get('seed')} | "
        f"validation: {validation} | source rows copied: {copied}",
        file=sys.stderr,
    )
