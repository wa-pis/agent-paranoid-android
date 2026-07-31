"""Human and JSON presentation helpers for the public CLI."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from pydantic import BaseModel, ValidationError

from test_data_agent.agent import (
    AgentGenerationSummary,
    AgentPlanSummary,
    AgentRecoverySummary,
    AgentResult,
    AgentReviewReport,
    AgentReviewState,
    AgentWorkspaceStatus,
)
from test_data_agent.audit import AuditVerificationResult
from test_data_agent.cli_contract import CliErrorCode, DoctorReport
from test_data_agent.cli_parser import write_cli_error_response
from test_data_agent.validation import DatasetValidationReport


def friendly_error(exc: Exception) -> str:
    """Return a bounded, user-facing validation error."""
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ()))
        message = first.get("msg", str(exc))
        return f"{location}: {message}" if location else message
    return str(exc)


def report_cli_error(
    args: argparse.Namespace,
    *,
    code: CliErrorCode,
    message: str,
    help_command: str | None = None,
    exit_code: int = 2,
) -> int:
    """Render a CLI failure in the requested human or JSON format."""
    if getattr(args, "json_output", False):
        write_cli_error_response(
            code=code,
            message=message,
            command=f"test-data-agent {args.command}",
            help_command=help_command,
            exit_code=exit_code,
        )
        return exit_code
    print(f"Error: {message}", file=sys.stderr)
    if help_command is not None:
        print(f"Run '{help_command}' for examples and options.", file=sys.stderr)
    return exit_code


def write_validation_result(
    report: DatasetValidationReport,
    output: Path | None,
) -> int:
    """Render validation output and return its public exit code."""
    failed = sum(section.failed for section in report.sections)
    passed = sum(section.passed for section in report.sections)
    status = "passed" if report.valid else "failed"
    destination = f" Report: {output}" if output is not None else ""
    print(
        f"Validation {status}: {passed} checks passed, {failed} failed."
        f"{destination}",
        file=sys.stderr,
    )
    if output is None:
        print(report.model_dump_json(indent=2))
    return 0 if report.valid else 1


def write_json_document(document: BaseModel) -> None:
    """Write one public Pydantic document as formatted JSON."""
    print(document.model_dump_json(indent=2))


def write_examples(examples_text: str) -> int:
    """Write copy-ready workflow examples."""
    print(examples_text)
    return 0


def write_audit_verification_result(result: AuditVerificationResult) -> int:
    """Write a successful audit verification summary."""
    print(
        f"Audit log verified: {result.record_count} records, "
        f"last MAC {result.last_mac}",
        file=sys.stderr,
    )
    return 0


def write_doctor_report(report: DoctorReport) -> int:
    """Write installation checks and return their public exit code."""
    for check in report.checks:
        print(check, file=sys.stderr)
    for failure in report.failures:
        print(f"doctor failed: {failure}", file=sys.stderr)
    if report.failures:
        return 1
    print("doctor passed", file=sys.stderr)
    return 0


def write_agent_command_result(result: AgentResult, *, json_output: bool) -> None:
    """Render a plan or generation result in the requested format."""
    if json_output:
        write_json_document(result)
    else:
        write_agent_result_summary(result)


def write_agent_status_result(
    status: AgentWorkspaceStatus,
    *,
    json_output: bool,
    pending_heading: str = "Agent status: awaiting approval",
) -> None:
    """Render an agent workspace status in the requested format."""
    if json_output:
        write_json_document(status)
    else:
        write_agent_status_summary(status, pending_heading=pending_heading)


def write_agent_review_result(
    report: AgentReviewReport,
    *,
    json_output: bool,
) -> None:
    """Render a metadata-only review in the requested format."""
    if json_output:
        write_json_document(report)
    else:
        write_agent_review_report(report)


def write_agent_result_summary(result: AgentResult) -> None:
    """Write a human-readable agent plan or generation summary."""
    if result.phase.value == "awaiting_approval":
        if not isinstance(result.summary, AgentPlanSummary):
            raise ValueError("awaiting-approval result is missing its plan summary")
        write_agent_plan_review(
            heading="Agent plan ready",
            summary=result.summary,
            workspace=result.artifacts.workspace,
            spec_path=result.artifacts.dataset_spec_path,
            review=result.review,
        )
        return
    if not isinstance(result.summary, AgentGenerationSummary):
        raise ValueError("completed agent result is missing its generation summary")
    row_counts = result.summary.row_counts
    rows_text = ", ".join(f"{name}={count}" for name, count in row_counts.items()) or "no rows"
    validation = "passed" if result.summary.validation_valid else "failed"
    print(
        "Agent generation completed: "
        f"{result.artifacts.generated_folder} | rows: {rows_text} | "
        f"seed: {result.summary.seed} | validation: {validation} | "
        "source rows copied: no | "
        f"approval receipt: {result.artifacts.approval_receipt_path}",
        file=sys.stderr,
    )


def write_agent_status_summary(
    status: AgentWorkspaceStatus,
    *,
    pending_heading: str = "Agent status: awaiting approval",
) -> None:
    """Write a human-readable agent workspace status."""
    if status.phase.value == "awaiting_approval":
        if not isinstance(status.summary, AgentPlanSummary):
            raise ValueError("awaiting-approval status is missing its plan summary")
        write_agent_plan_review(
            heading=pending_heading,
            summary=status.summary,
            workspace=status.artifacts.workspace,
            spec_path=status.artifacts.dataset_spec_path,
            review=status.review,
        )
        return
    if status.phase.value == "recovery_required":
        if not isinstance(status.summary, AgentRecoverySummary):
            raise ValueError("recovery-required status is missing its recovery summary")
        workspace_command = display_untrusted_name(
            shlex.quote(str(status.artifacts.workspace)),
            limit=260,
        )
        print(
            "Agent status: recovery required | generated rows will not be regenerated",
            file=sys.stderr,
        )
        print(
            f"Recover: test-data-agent agent-recover {workspace_command} "
            f"--reviewed-spec-sha256 {status.summary.reviewed_spec_sha256}",
            file=sys.stderr,
        )
        return
    if not isinstance(status.summary, AgentGenerationSummary):
        raise ValueError("completed agent status is missing its generation summary")
    validation = "passed" if status.summary.validation_valid else "failed"
    print(
        "Agent status: completed | "
        f"output: {status.artifacts.generated_folder} | "
        f"validation: {validation} | source rows copied: no",
        file=sys.stderr,
    )


def write_agent_review_report(report: AgentReviewReport) -> None:
    """Write a bounded metadata-only DatasetSpec review."""
    workspace_text = display_untrusted_name(str(report.workspace), limit=240)
    workspace_command = display_untrusted_name(
        shlex.quote(str(report.workspace)),
        limit=260,
    )
    spec_path_text = display_untrusted_name(
        str(report.dataset_spec_path),
        limit=240,
    )
    print(f"DatasetSpec review: {workspace_text}", file=sys.stderr)
    print(
        f"Spec: {spec_path_text} | source: "
        f"{display_untrusted_name(report.source_type)} | seed: {report.seed} | "
        f"format: {report.output_format.value}",
        file=sys.stderr,
    )
    changed = "yes" if report.spec_changed_since_plan else "no"
    print(
        f"Plan ID: {report.plan_id} | changed since plan: {changed}",
        file=sys.stderr,
    )
    print(
        f"Current spec SHA-256: {report.current_spec_sha256}",
        file=sys.stderr,
    )
    raw_values = (
        "blocked"
        if report.safety.raw_sensitive_values_blocked
        else "ALLOWED - do not approve"
    )
    unknown_fields = (
        "sensitive"
        if report.safety.unknown_fields_treated_as_sensitive
        else "not sensitive - review required"
    )
    print(
        f"Privacy: raw sensitive values {raw_values} | unknown fields "
        f"{unknown_fields} | sensitive fields: "
        f"{report.safety.sensitive_field_count} | privacy rules: "
        f"{report.safety.privacy_rule_count}",
        file=sys.stderr,
    )
    print("Entities:", file=sys.stderr)
    for entity in report.entities:
        primary_key = (
            display_untrusted_name(entity.primary_key)
            if entity.primary_key is not None
            else "none"
        )
        print(
            f"  {display_untrusted_name(entity.name)}: {entity.row_count} rows | "
            f"primary key: {primary_key}",
            file=sys.stderr,
        )
        for field in entity.fields[:20]:
            flags = [
                (
                    f"nullable {field.null_ratio:.2f}"
                    if field.nullable
                    else "required"
                )
            ]
            if field.sensitive:
                flags.append("sensitive")
            if field.is_identifier:
                flags.append("identifier")
            if field.semantic_type is not None:
                flags.append(
                    f"semantic={display_untrusted_name(field.semantic_type)}"
                )
            if field.distribution_kind is not None:
                flags.append(
                    "distribution="
                    f"{display_untrusted_name(field.distribution_kind)}"
                )
            print(
                f"    {display_untrusted_name(field.name)}: "
                f"{field.data_type.value} | {' | '.join(flags)}",
                file=sys.stderr,
            )
        omitted = len(entity.fields) - 20
        if omitted > 0:
            print(
                f"    +{omitted} more fields; inspect dataset_spec.yaml",
                file=sys.stderr,
            )
    if report.relationships:
        print("Relationships:", file=sys.stderr)
        for relationship in report.relationships:
            child = (
                f"{display_untrusted_name(relationship.child_entity)}."
                f"{display_untrusted_name(relationship.child_field)}"
            )
            parent = (
                f"{display_untrusted_name(relationship.parent_entity)}."
                f"{display_untrusted_name(relationship.parent_field)}"
            )
            print(
                f"  {child} -> {parent} | "
                f"{relationship.relationship_type.value} | "
                f"confidence: {relationship.confidence:.2f}",
                file=sys.stderr,
            )
    print(f"Constraints: {report.constraint_count}", file=sys.stderr)
    for assumption in report.assumptions:
        print(f"Assumption: {assumption}", file=sys.stderr)
    for warning in report.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print("Approve only after reviewing the complete DatasetSpec:", file=sys.stderr)
    print(
        f"  test-data-agent agent-approve {workspace_command} "
        f"--reviewed-spec-sha256 {report.current_spec_sha256}",
        file=sys.stderr,
    )
    print(
        "Optional AI advice (review the changed spec again before approval):",
        file=sys.stderr,
    )
    print(
        f"  test-data-agent agent-advise {workspace_command} --provider openai",
        file=sys.stderr,
    )


def write_agent_plan_review(
    *,
    heading: str,
    summary: AgentPlanSummary,
    workspace: Path,
    spec_path: Path,
    review: AgentReviewState | None,
) -> None:
    """Write a bounded human review of a pending agent plan."""
    workspace_text = display_untrusted_name(str(workspace), limit=240)
    workspace_command = display_untrusted_name(shlex.quote(str(workspace)), limit=260)
    spec_path_text = display_untrusted_name(str(spec_path), limit=240)
    print(f"{heading}: {workspace_text}", file=sys.stderr)
    print(
        f"Source: {display_untrusted_name(summary.source_type)} | seed: {summary.seed} | "
        f"format: {summary.output_format.value}",
        file=sys.stderr,
    )
    print("Entities:", file=sys.stderr)
    for entity in summary.entities:
        fields = [
            f"{display_untrusted_name(field.name)}:{field.data_type.value}"
            for field in entity.fields
        ]
        print(
            f"  {display_untrusted_name(entity.name)}: {entity.row_count} rows | "
            f"fields ({entity.field_count}): {format_review_items(fields)}",
            file=sys.stderr,
        )
    sensitive = [
        f"{display_untrusted_name(field.entity)}.{display_untrusted_name(field.field)}"
        for field in summary.sensitive_fields
    ]
    print(
        f"Sensitive fields: {format_review_items(sensitive) if sensitive else 'none detected'}",
        file=sys.stderr,
    )
    if summary.relationships:
        print("Relationships:", file=sys.stderr)
        for relationship in summary.relationships:
            child = (
                f"{display_untrusted_name(relationship.child_entity)}."
                f"{display_untrusted_name(relationship.child_field)}"
            )
            parent = (
                f"{display_untrusted_name(relationship.parent_entity)}."
                f"{display_untrusted_name(relationship.parent_field)}"
            )
            print(
                f"  {child} -> {parent} | {relationship.relationship_type.value} | "
                f"confidence: {relationship.confidence:.2f}",
                file=sys.stderr,
            )
    for assumption in summary.assumptions:
        print(f"Assumption: {assumption}", file=sys.stderr)
    for warning in summary.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"Review: {spec_path_text}", file=sys.stderr)
    if review is None:
        print(
            "Approve unavailable: create a new plan with fingerprint-bound approval.",
            file=sys.stderr,
        )
        return
    print(
        f"Plan ID: {review.plan_id} | current spec SHA-256: "
        f"{review.current_spec_sha256}",
        file=sys.stderr,
    )
    if review.spec_changed_since_plan:
        print("Notice: DatasetSpec changed since the initial plan.", file=sys.stderr)
    print(
        f"Next: test-data-agent agent-review {workspace_command}",
        file=sys.stderr,
    )


def display_untrusted_name(value: str, *, limit: int = 80) -> str:
    """Escape and bound untrusted names before terminal presentation."""
    truncated = value[:limit]
    escaped = json.dumps(truncated, ensure_ascii=False)[1:-1]
    return f"{escaped}..." if len(value) > limit else escaped


def format_review_items(items: list[str], *, limit: int = 8) -> str:
    """Bound long metadata lists in human review output."""
    if not items:
        return "none"
    visible = items[:limit]
    suffix = f", +{len(items) - limit} more" if len(items) > limit else ""
    return ", ".join(visible) + suffix
