"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from test_data_agent.adapters import (
    csv_file_to_dataset_profile,
    csv_file_to_dataset_spec,
    dataset_spec_to_generation_spec,
)
from test_data_agent.business_rules import load_business_rules
from test_data_agent.business_validator import validate_business_rules
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.generator import generate_rows
from test_data_agent.profiling import profile_example_folder
from test_data_agent.rules_engine import GenerationMode, apply_business_rules
from test_data_agent.spec import GenerationSpec, OutputFormat
from test_data_agent.validation import validate_dataset
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
    validate_parser.add_argument("--output", "-o", type=Path)

    generate_example_parser = subparsers.add_parser("generate-from-example")
    generate_example_parser.add_argument("input_folder", type=Path)
    generate_example_parser.add_argument("--output", "-o", type=Path, required=True)
    generate_example_parser.add_argument("--seed", type=int, required=True)
    generate_example_parser.add_argument("--count", type=int)
    generate_example_parser.add_argument("--format", choices=[item.value for item in OutputFormat], required=True, dest="output_format")
    generate_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"))
    generate_example_parser.add_argument("--no-cache", action="store_true")
    generate_example_parser.add_argument("--rule-sample-rows", type=int, default=50_000)

    args = parser.parse_args(argv)

    if args.command == "generate":
        if args.spec is not None and is_dataset_spec_path(args.spec):
            return generate_dataset_command(args)
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

    if args.command == "profile-example":
        profile = profile_example_folder(
            args.input_folder,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
            rule_sample_rows=args.rule_sample_rows,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(profile.model_dump_json(indent=2))
        return 0

    if args.command == "infer-spec":
        profile = DatasetProfile.model_validate_json(args.profile.read_text())
        spec = infer_dataset_spec(profile, count=args.count)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(dataset_spec_to_yaml(spec))
        return 0

    if args.command == "profile-csv":
        profile = csv_file_to_dataset_profile(args.input, table_name=args.table)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(profile.model_dump_json(indent=2))
        return 0

    if args.command == "generate-from-csv":
        profile = csv_file_to_dataset_profile(args.input, table_name=args.table)
        spec = csv_file_to_dataset_spec(args.input, table_name=args.table, count=args.count, seed=args.seed)
        spec.generation_settings.seed = args.seed
        spec.generation_settings.output_format = CoreOutputFormat(args.output_format)
        apply_dataset_mode_options(spec, args.mode, args.invalid_ratio)
        legacy_spec = dataset_spec_to_generation_spec(spec, seed=args.seed, output_format=OutputFormat(args.output_format))
        apply_mode_options(legacy_spec, args.mode, args.invalid_ratio)
        rows = generate_rows(legacy_spec)
        rows_by_entity = {spec.entities[0].name: rows}
        business_report = apply_business_rules_from_args(rows_by_entity, args, args.seed)
        report = validate_dataset(rows_by_entity, spec)
        if args.output is None:
            raise SystemExit("CSV generation requires --output")
        write_single_entity_rows(rows_by_entity, OutputFormat(args.output_format), args.output)
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
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text)
            else:
                print(text)
            return 0 if report.valid else 1
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
        output_format = OutputFormat(args.output_format)
        write_dataset_rows(rows_by_entity, output_format, args.output)
        report = validate_dataset(rows_by_entity, spec)
        (args.output / "profile.json").write_text(profile.model_dump_json(indent=2))
        (args.output / "dataset_spec.yaml").write_text(dataset_spec_to_yaml(spec))
        (args.output / "validation_report.json").write_text(report.model_dump_json(indent=2))
        return 0 if report.valid else 1

    return 2


def load_spec(path: Path) -> GenerationSpec:
    return GenerationSpec.model_validate_json(path.read_text())


def is_dataset_spec_path(path: Path) -> bool:
    return path.suffix.lower() in {".yaml", ".yml"}


def load_dataset_spec(path: Path) -> DatasetSpec:
    return DatasetSpec.model_validate(yaml.safe_load(path.read_text()) or {})


def dataset_spec_to_yaml(spec: DatasetSpec) -> str:
    return yaml.safe_dump(spec.model_dump(mode="json"), sort_keys=False)


def generate_dataset_command(args: argparse.Namespace) -> int:
    spec = load_dataset_spec(args.spec)
    output_format = OutputFormat(args.output_format or "csv")
    if args.count is not None:
        for entity in spec.entities:
            entity.row_count = args.count
    rows_by_entity = generate_dataset(spec, seed=args.seed or 0)
    if args.output is None:
        raise SystemExit("dataset generation requires --output folder")
    write_dataset_rows(rows_by_entity, output_format, args.output)
    report = validate_dataset(rows_by_entity, spec)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "validation_report.json").write_text(report.model_dump_json(indent=2))
    return 0 if report.valid else 1


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


def write_dataset_generation_artifacts(
    profile: DatasetProfile,
    spec: DatasetSpec,
    report: Any,
    output: Path,
    business_report: Any | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    (output.parent / "csv_profile.json").write_text(profile.model_dump_json(indent=2))
    artifact_dir = output.parent
    (artifact_dir / "generation_spec.json").write_text(spec.model_dump_json(indent=2))
    (artifact_dir / "validation_report.json").write_text(report.model_dump_json(indent=2))
    if business_report is not None:
        (artifact_dir / "business_validation_report.json").write_text(business_report.model_dump_json(indent=2))


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


def write_dataset_rows(rows_by_entity: dict[str, list[dict[str, Any]]], output_format: OutputFormat, output_folder: Path) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    for entity_name, rows in rows_by_entity.items():
        if output_format == OutputFormat.CSV:
            (output_folder / f"{entity_name}.csv").write_text(rows_to_csv(rows))
        elif output_format == OutputFormat.JSON:
            (output_folder / f"{entity_name}.json").write_text(json.dumps(rows, indent=2, sort_keys=True))
        elif output_format == OutputFormat.PARQUET:
            write_parquet(rows, output_folder / f"{entity_name}.parquet")


def write_single_entity_rows(rows_by_entity: dict[str, list[dict[str, Any]]], output_format: OutputFormat, output: Path) -> None:
    if len(rows_by_entity) != 1:
        raise SystemExit("single-entity output requires exactly one generated entity")
    rows = next(iter(rows_by_entity.values()))
    if output_format == OutputFormat.CSV:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rows_to_csv(rows))
    elif output_format == OutputFormat.JSON:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2, sort_keys=True))
    elif output_format == OutputFormat.PARQUET:
        write_parquet(rows, output)


def load_dataset_rows(input_folder: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(input_folder.iterdir()):
        if path.suffix == ".csv":
            with path.open(newline="") as handle:
                rows_by_entity[path.stem] = [dict(row) for row in csv.DictReader(handle)]
        elif path.suffix == ".json":
            rows_by_entity[path.stem] = json.loads(path.read_text())
        elif path.suffix == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise SystemExit("Parquet input requires pyarrow") from exc
            rows_by_entity[path.stem] = pq.read_table(path).to_pylist()
    return rows_by_entity


if __name__ == "__main__":
    raise SystemExit(main())
