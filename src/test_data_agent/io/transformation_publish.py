"""Closed development-only publication for fictional temporary test storage.

No public CLI/Python facade/MCP wiring; retained test destinations are private.
Only fictional test requests are authorized before activation review.
"""

import json
import os
from test_data_agent.io.transformation_input import source_reader
from test_data_agent.core.transformation_limits import (
    InputDimension, TransformationLimitError, resolve_input_limit,
)
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.path_policy import (
    atomic_write_bytes, make_staging_directory, publish_directory,
    PathIdentity, path_identity, remove_tree_if_identity,
)
from test_data_agent.io.transformation_execute import replace_csv_snapshot
from test_data_agent.io.transformation_sql import render_transformation_sql
from test_data_agent.io.transformation_parquet import render_transformation_parquet
from test_data_agent.core.transformation_policy import SqlOutput, ParquetOutput
from test_data_agent.csv_profiler import validate_csv_headers
from test_data_agent.io.transformation_source import prepare_csv_review_from_paths


class TransformationPublicationError(ValueError):
    """Value-free failure in private temporary publication."""


class TransformationCleanupError(TransformationPublicationError):
    """Publication failed and artifact removal could not be confirmed."""


def _publish_test_bundle(destination: Path, filename: str, payload: bytes,
                         manifest: bytes, budget: GenerationBudget, *,
                         max_output_bytes: int) -> None:
    """Closed fictional-test writer; no public execution or approval authority."""
    if filename not in {"dataset.csv", "dataset.parquet", "dataset.sql"}:
        raise ValueError("invalid transformation artifact name")
    if type(max_output_bytes) is not int or not 0 < max_output_bytes <= 2**63 - 1:
        raise ValueError("invalid transformation output budget")
    if len(payload) + len(manifest) > max_output_bytes:
        raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
            len(payload) + len(manifest), max_output_bytes, "bundle_run")
    budget.check("temporary transformation publication")
    staging = make_staging_directory(destination)
    staging_identity: PathIdentity | None = None
    try:
        staging_identity = path_identity(staging)
        atomic_write_bytes(staging / filename, payload)
        atomic_write_bytes(staging / "manifest.json", manifest)
        budget.check("temporary transformation publication")
        publish_directory(staging, destination)
    except BaseException:
        # Rename may have committed before its directory fsync failed.
        # Never remove a replaced or pre-existing destination.
        try:
            if staging_identity is None:
                raise ValueError("staging identity not confirmed")
            remove_tree_if_identity(destination, staging_identity)
            remove_tree_if_identity(staging, staging_identity)
        except (OSError, ValueError):
            try:
                raise TransformationCleanupError(
                    "transformation publication failed; cleanup incomplete; output or staging may remain; "
                    "inspect the selected destination before retrying")
            except TransformationCleanupError as error:
                error.__context__ = None
                raise
        raise


def _execute_reviewed_test_from_paths(
    source_path: Path, table_name: str, policy_path: Path, destination: Path, *,
    expected_snapshot_sha256: str, max_total_bytes: int | None, max_review_bytes: int,
    max_output_bytes: int | None, budget: GenerationBudget, receipt_path: Path | None = None,
) -> dict[str, object]:
    """Closed fictional-test command; validate fixed review before publication.

    The expected review digest detects drift; it never substitutes for a receipt.
    No receipt creation, public command or database access.
    """
    try:
        budget.check("temporary transformation command")
        if (type(expected_snapshot_sha256) is not str
                or len(expected_snapshot_sha256) != 64
                or any(char not in "0123456789abcdef" for char in expected_snapshot_sha256)):
            raise ValueError
        request = prepare_csv_review_from_paths(source_path, table_name,
            policy_path.parent.absolute(), policy_path.name,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
        if request.snapshot_sha256 != expected_snapshot_sha256:
            raise ValueError
        policy_payload = next(part.payload for part in request.parts if part.kind == "policy")
        policy = load_behavior_policy_yaml(policy_payload,
            max_bytes=max_total_bytes or len(policy_payload), budget=budget)
        if max_total_bytes is None:
            max_total_bytes = resolve_input_limit(InputDimension.TOTAL_BYTES,
                policy.resource_limits, os.environ).value
        output_ceiling = resolve_input_limit(InputDimension.OUTPUT_BYTES, policy.resource_limits, os.environ)
        output_limit = output_ceiling.value if max_output_bytes is None else max_output_bytes
        manifest = _publish_reviewed_test_snapshot(request, destination, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, max_output_bytes=output_limit,
            budget=budget, receipt_path=receipt_path)
        return {"status": "closed_test_completed", "snapshot_sha256": request.snapshot_sha256,
                "provenance": manifest["provenance"], "output_budget": {
                    "run_bytes": output_limit, "ceiling_bytes": output_ceiling.value,
                    "ceiling_origin": output_ceiling.origin}}
    except (TransformationLimitError, TransformationCleanupError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        pass
    try:
        raise TransformationPublicationError("invalid temporary transformation command")
    except TransformationPublicationError as error:
        error.__context__ = None
        raise


def _run_temporary_transform(
    source_path: Path, table_name: str, policy_path: Path, *,
    expected_snapshot_sha256: str, max_total_bytes: int, max_review_bytes: int,
    max_output_bytes: int, budget: GenerationBudget, receipt_path: Path | None = None,
) -> dict[str, object]:
    """Unregistered fictional command; discard all artifacts before returning."""
    with TemporaryDirectory(prefix="apa-fictional-transform-") as temporary:
        summary = _execute_reviewed_test_from_paths(source_path, table_name, policy_path,
            Path(temporary).resolve() / "output", expected_snapshot_sha256=expected_snapshot_sha256,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
            max_output_bytes=max_output_bytes, budget=budget, receipt_path=receipt_path)
    budget.check("temporary transformation command completed")
    return {**summary, "status": "temporary_test_completed"}


def _publish_reviewed_test_snapshot(
    request: ApprovalRequest, destination: Path, *, max_total_bytes: int,
    max_review_bytes: int, max_output_bytes: int, budget: GenerationBudget,
    receipt_path: Path | None = None,
) -> dict[str, object]:
    """Closed fictional-test execution; canonical review and receipts enforced."""
    try:
        result = replace_csv_snapshot(request, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, max_output_bytes=max_output_bytes,
            budget=budget, receipt_path=receipt_path)
        policy = load_behavior_policy_yaml(
            next(part.payload for part in request.parts if part.kind == "policy"),
            max_bytes=max_total_bytes, budget=budget)
        source = next(part for part in request.parts if part.kind == "source")
        reader = source_reader(source, policy, budget=budget)
        reader.fieldnames = validate_csv_headers(reader.fieldnames)
        source_rows = (tuple(None if row[name] == policy.csv_nulls.input_token else row[name]
                             for name in result.columns) for row in reader)
        original_rows = source_rows if tuple(reader.fieldnames) == result.columns else None
        if isinstance(policy.output, SqlOutput):
            payload = render_transformation_sql(result, policy.output,
                max_bytes=max_output_bytes, budget=budget, source_rows=original_rows)
            filename = "dataset.sql"
        elif isinstance(policy.output, ParquetOutput):
            payload = render_transformation_parquet(result, policy.output,
                max_bytes=max_output_bytes, budget=budget, source_rows=original_rows)
            filename = "dataset.parquet"
        else:
            payload, filename = result.csv_bytes, "dataset.csv"
        if result.provenance is None:
            raise ValueError
        summary: dict[str, object] = {"version": 2, "origin": "transformed_mixed",
            "output": policy.output.review_summary() if policy.output else {"format": "csv"},
            "privacy_notice": "Mixed-origin output may retain source information; not anonymized.",
            "fields": [{"entity": item.entity, "field": item.field,
                        "action": item.behavior.action,
                        "unmatched": getattr(getattr(item.behavior, "unmatched", None), "action", None)}
                       for item in policy.fields],
            "provenance": asdict(result.provenance)}
        manifest = json.dumps(summary, ensure_ascii=True, sort_keys=True).encode("ascii")
        _publish_test_bundle(destination, filename, payload, manifest, budget,
                             max_output_bytes=max_output_bytes)
        return summary
    except (TransformationLimitError, TransformationCleanupError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, StopIteration):
        pass
    try:
        raise TransformationPublicationError("invalid temporary transformation publication")
    except TransformationPublicationError as error:
        error.__context__ = None
        raise


@contextmanager
def temporary_csv_publication(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int,
    max_output_bytes: int, budget: GenerationBudget, receipt_path: Path | None = None,
) -> Iterator[Path]:
    """Yield a complete private test artifact directory; delete it on exit."""
    with TemporaryDirectory(prefix="apa-fictional-transform-") as temporary:
        destination = Path(temporary).resolve() / "output"
        _publish_reviewed_test_snapshot(request, destination, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, max_output_bytes=max_output_bytes,
            budget=budget, receipt_path=receipt_path)
        yield destination
