"""Command helpers for deprecated GenerationSpec CLI flows."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Callable

from test_data_agent.compat.legacy_workflows import (
    generate_legacy_spec_artifacts,
    validate_legacy_spec_artifacts,
)
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.commands import should_fail_generation


BusinessRulesApplier = Callable[[dict[str, list[dict[str, Any]]], int], Any | None]


def generate_legacy_command(
    args: argparse.Namespace,
    *,
    business_rules_applier: BusinessRulesApplier | None = None,
) -> int:
    legacy_result, business_report = generate_legacy_spec_artifacts(
        args.spec,
        row_count=args.count,
        seed=args.seed,
        output_format=None if args.output_format is None else OutputFormat(args.output_format),
        output_path=args.output,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
        business_rules_applier=business_rules_applier,
    )
    if should_fail_generation(legacy_result.report, business_report, args.mode):
        for error in legacy_result.report.errors:
            print(error, file=sys.stderr)
        if business_report is not None and not business_report.valid:
            print("business validation failed", file=sys.stderr)
        return 1
    return 0


def validate_legacy_command(args: argparse.Namespace) -> int:
    report = validate_legacy_spec_artifacts(
        args.spec,
        args.rows,
        output_path=args.output,
    )
    return 0 if report.valid else 1


__all__ = [
    "generate_legacy_command",
    "validate_legacy_command",
]
