"""CLI handlers for dataset and utility commands."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from typing import Any, Protocol

from test_data_agent.audit import verify_audit_log_from_env
from test_data_agent.cli_contract import DoctorReport
from test_data_agent.cli_dependencies import DEFAULT_CLI_DEPENDENCY_RESOLVER
from test_data_agent.cli_presenter import (
    write_audit_verification_result,
    write_doctor_report,
    write_examples,
    write_shell_completion,
    write_validation_result,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.demo import run_demo
from test_data_agent.generation.constraint_solver import default_value_for_field
from test_data_agent.io import (
    generate_dataset_from_csv_command,
    generate_dataset_from_example_command,
    generate_dataset_from_profile_command,
    generate_dataset_command,
    export_postgres_sql_command,
    infer_dataset_spec_command,
    profile_postgres_command,
    profile_csv_command,
    profile_example_command,
    validate_dataset_artifacts,
    write_generation_summary,
)
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path

BusinessRulesApplier = Callable[
    [dict[str, list[dict[str, Any]]], argparse.Namespace, int, DatasetSpec | None],
    Any | None,
]


class DoctorInspector(Protocol):
    def __call__(
        self,
        *,
        skip_smoke: bool = False,
        required_extras: set[str] | None = None,
    ) -> DoctorReport: ...


def run_dataset_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int | None:
    """Run one dataset command, or return ``None`` when it is not dataset-owned."""

    business_rules_applier = business_rules_applier or apply_business_rules_from_args

    def apply_rules(
        rows_by_entity: dict[str, list[dict[str, Any]]],
        seed: int,
        spec: DatasetSpec | None,
    ) -> Any | None:
        return business_rules_applier(rows_by_entity, args, seed, spec)

    if args.command == "generate":
        if args.profile is not None:
            return generate_dataset_from_profile_command(
                args,
                business_rules_applier=apply_rules,
            )
        return generate_dataset_command(
            args,
            business_rules_applier=apply_rules,
        )

    if args.command == "export-postgres-sql":
        return export_postgres_sql_command(args)

    if args.command in {"profile-example", "profile-csv-folder"}:
        return profile_example_command(args)

    if args.command == "infer-spec":
        return infer_dataset_spec_command(args)

    if args.command == "profile-csv":
        return profile_csv_command(args)

    if args.command == "profile-postgres":
        driver = DEFAULT_CLI_DEPENDENCY_RESOLVER.require_module(
            "psycopg",
            extra="postgres",
            purpose="PostgreSQL profiling",
        )
        return profile_postgres_command(args, driver=driver)

    if args.command == "generate-from-csv":
        return generate_dataset_from_csv_command(
            args,
            business_rules_applier=apply_rules,
        )

    if args.command == "validate":
        report = validate_dataset_artifacts(
            args.spec,
            args.rows,
            output_path=args.output,
            overwrite=args.overwrite,
        )
        return write_validation_result(report, args.output)

    if args.command in {"generate-from-example", "generate-from-csv-folder"}:
        return generate_dataset_from_example_command(args)

    return None


def run_utility_command(
    args: argparse.Namespace,
    *,
    examples_text: str,
    doctor_inspector: DoctorInspector,
) -> int | None:
    """Run one utility command, or return ``None`` when it is not utility-owned."""

    if args.command == "examples":
        return write_examples(examples_text)

    if args.command == "completion":
        return write_shell_completion(
            args.shell,
            args.completion_commands,
            args.completion_options,
        )

    if args.command == "demo":
        exit_code = run_demo(args.output)
        write_generation_summary(args.output)
        return exit_code

    if args.command == "doctor":
        return write_doctor_report(
            doctor_inspector(
                skip_smoke=args.skip_smoke,
                required_extras=set(args.require_extra),
            ),
            json_output=getattr(args, "json_output", False),
        )

    if args.command == "audit-verify":
        audit_result = verify_audit_log_from_env(args.log)
        return write_audit_verification_result(audit_result)

    return None


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
