"""Closed development-only publication in automatically deleted test storage.

No caller-selected destination and no public CLI/Python facade/MCP wiring.
Only fictional test requests are authorized before activation review.
"""

import json
from test_data_agent.io.transformation_input import source_reader
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.path_policy import atomic_write_bytes, make_staging_directory, publish_directory
from test_data_agent.io.transformation_execute import replace_csv_snapshot
from test_data_agent.io.transformation_sql import render_transformation_sql
from test_data_agent.io.transformation_parquet import render_transformation_parquet
from test_data_agent.core.transformation_policy import SqlOutput, ParquetOutput
from test_data_agent.csv_profiler import validate_csv_headers


class TransformationPublicationError(ValueError):
    """Value-free failure in private temporary publication."""


@contextmanager
def temporary_csv_publication(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int,
    max_output_bytes: int, budget: GenerationBudget, receipt_path: Path | None = None,
) -> Iterator[Path]:
    """Yield a complete private test artifact directory; delete it on exit."""
    with TemporaryDirectory(prefix="apa-fictional-transform-") as temporary:
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
            manifest = json.dumps({"version": 1, "origin": "transformed_mixed",
                "output": policy.output.review_summary() if policy.output else {"format": "csv"},
                "privacy_notice": "Mixed-origin output may retain source information; not anonymized.",
                "fields": [{"entity": item.entity, "field": item.field,
                            "action": item.behavior.action,
                            "unmatched": getattr(getattr(item.behavior, "unmatched", None), "action", None)}
                           for item in policy.fields],
                "retention": asdict(result.retention)}, ensure_ascii=True, sort_keys=True).encode("ascii")
            if len(manifest) + len(payload) > max_output_bytes:
                raise ValueError
            budget.check("temporary transformation publication")
            destination = Path(temporary).resolve() / "output"
            staging = make_staging_directory(destination)
            atomic_write_bytes(staging / filename, payload)
            atomic_write_bytes(staging / "manifest.json", manifest)
            budget.check("temporary transformation publication")
            publish_directory(staging, destination)
        except (OSError, ValueError, TypeError, AttributeError, StopIteration):
            failed = True
        else:
            failed = False
        if failed:
            try:
                raise TransformationPublicationError("invalid temporary transformation publication")
            except TransformationPublicationError as error:
                error.__context__ = None
                raise
        yield destination
