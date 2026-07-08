"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from test_data_agent.business_rules import load_business_rules
from test_data_agent.business_validator import validate_business_rules
from test_data_agent.csv_profiler import profile_csv
from test_data_agent.generator import generate_rows
from test_data_agent.rules_engine import GenerationMode, apply_business_rules
from test_data_agent.spec import GenerationSpec, OutputFormat
from test_data_agent.validator import validate_rows_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="test-data-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("spec", nargs="?", type=Path)
    generate_parser.add_argument("--profile", type=Path)
    generate_parser.add_argument("--count", type=int)
    generate_parser.add_argument("--mode", choices=[item.value for item in GenerationMode], default="valid")
    generate_parser.add_argument("--invalid-ratio", type=float, default=0.0)
    generate_parser.add_argument("--seed", type=int)
    generate_parser.add_argument("--format", choices=[item.value for item in OutputFormat], dest="output_format")
    generate_parser.add_argument("--output", "-o", type=Path)
    generate_parser.add_argument("--business-rules", type=Path)

    profile_csv_parser = subparsers.add_parser("profile-csv")
    profile_csv_parser.add_argument("input", type=Path)
    profile_csv_parser.add_argument("--table", type=str)
    profile_csv_parser.add_argument("--output", "-o", type=Path, required=True)

    generate_csv_parser = subparsers.add_parser("generate-from-csv")
    generate_csv_parser.add_argument("input", type=Path)
    generate_csv_parser.add_argument("--count", type=int, required=True)
    generate_csv_parser.add_argument("--mode", choices=[item.value for item in GenerationMode], default="valid")
    generate_csv_parser.add_argument("--invalid-ratio", type=float, default=0.0)
    generate_csv_parser.add_argument("--seed", type=int, required=True)
    generate_csv_parser.add_argument("--format", choices=[item.value for item in OutputFormat], required=True, dest="output_format")
    generate_csv_parser.add_argument("--output", "-o", type=Path, required=True)
    generate_csv_parser.add_argument("--table", type=str)
    generate_csv_parser.add_argument("--business-rules", type=Path)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("spec", type=Path)
    validate_parser.add_argument("rows", type=Path)

    args = parser.parse_args(argv)

    if args.command == "generate":
        spec = build_generation_spec(args)
        rows = generate_rows(spec)
        business_report = apply_business_rules_from_args({spec.table.name: rows}, args, spec.seed)
        report = validate_rows_report(rows, spec)
        write_rows(rows, spec, args.output)
        write_generation_artifacts(spec, report, args.output, business_report=business_report)
        if should_fail_generation(report, business_report, args.mode):
            for error in report.errors:
                print(error, file=sys.stderr)
            if business_report is not None and not business_report.valid:
                print("business validation failed", file=sys.stderr)
            return 1
        return 0

    if args.command == "profile-csv":
        profile = profile_csv(args.input, table_name=args.table)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(profile.model_dump_json(indent=2))
        return 0

    if args.command == "generate-from-csv":
        profile = profile_csv(args.input, table_name=args.table)
        spec = GenerationSpec.from_csv_profile(
            profile.model_dump(),
            seed=args.seed,
            row_count=args.count,
        )
        spec.output_format = OutputFormat(args.output_format)
        apply_mode_options(spec, args.mode, args.invalid_ratio)
        rows = generate_rows(spec)
        business_report = apply_business_rules_from_args({spec.table.name: rows}, args, spec.seed)
        report = validate_rows_report(rows, spec)
        write_rows(rows, spec, args.output)
        write_csv_generation_artifacts(profile, spec, report, args.output, business_report=business_report)
        if should_fail_generation(report, business_report, args.mode):
            for error in report.errors:
                print(error, file=sys.stderr)
            if business_report is not None and not business_report.valid:
                print("business validation failed", file=sys.stderr)
            return 1
        return 0

    if args.command == "validate":
        spec = load_spec(args.spec)
        rows = json.loads(args.rows.read_text())
        report = validate_rows_report(rows, spec)
        print(report.model_dump_json(indent=2))
        if not report.valid:
            return 1
        return 0

    return 2


def load_spec(path: Path) -> GenerationSpec:
    return GenerationSpec.model_validate_json(path.read_text())


def build_generation_spec(args: argparse.Namespace) -> GenerationSpec:
    if args.profile is not None:
        if args.spec is not None:
            raise SystemExit("generate accepts either a spec path or --profile, not both")
        if args.count is None:
            raise SystemExit("--count is required with --profile")
        if args.seed is None:
            raise SystemExit("--seed is required with --profile")
        profile = json.loads(args.profile.read_text())
        spec = GenerationSpec.from_trino_profile(profile, seed=args.seed, row_count=args.count)
    else:
        if args.spec is None:
            raise SystemExit("generate requires a spec path or --profile")
        spec = load_spec(args.spec)
        if args.count is not None:
            spec.table.row_count = args.count
        if args.seed is not None:
            spec.seed = args.seed

    if args.output_format is not None:
        spec.output_format = OutputFormat(args.output_format)
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


def apply_business_rules_from_args(rows_by_table: dict[str, list[dict[str, Any]]], args: argparse.Namespace, seed: int) -> Any | None:
    rules_path = getattr(args, "business_rules", None)
    if rules_path is None:
        return None
    rules = load_business_rules(rules_path)
    apply_business_rules(rows_by_table, rules, seed=seed, mode=args.mode, invalid_ratio=args.invalid_ratio)
    return validate_business_rules(rows_by_table, rules)


def should_fail_generation(schema_report: Any, business_report: Any | None, mode: str) -> bool:
    if mode in {"mixed", "negative"}:
        return False
    if not schema_report.valid:
        return True
    return business_report is not None and not business_report.valid


def write_rows(rows: list[dict[str, Any]], spec: GenerationSpec, output: Path | None) -> None:
    if spec.output_format == "parquet":
        if output is None:
            raise SystemExit("Parquet output requires --output")
        write_parquet(rows, output)
        return

    if spec.output_format == "csv":
        text = rows_to_csv(rows)
    else:
        text = json.dumps(rows, indent=2, sort_keys=True)

    if output is None:
        print(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)


def write_generation_artifacts(spec: GenerationSpec, report: Any, output: Path | None, business_report: Any | None = None) -> None:
    artifact_dir = output.parent if output is not None else Path.cwd()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))


def write_csv_generation_artifacts(profile: Any, spec: GenerationSpec, report: Any, output: Path, business_report: Any | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    (output.parent / "csv_profile.json").write_text(profile.model_dump_json(indent=2))
    write_generation_artifacts(spec, report, output, business_report=business_report)


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def write_parquet(rows: list[dict[str, Any]], output: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit("Parquet output requires pyarrow") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    stable_rows = [
        {key: None if value is None else str(value) for key, value in row.items()}
        for row in rows
    ]
    pq.write_table(pa.Table.from_pylist(stable_rows), output)


if __name__ == "__main__":
    raise SystemExit(main())
