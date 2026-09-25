"""Closed CSV replacement prototype; not wired to public execution surfaces.

Development/tests only pending end-to-end safety review and activation gates.
Preservation requires an existing local receipt. No filesystem publication,
receipt minting or external access.
"""

import csv
import io
from pathlib import Path

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_FILE_BYTES, GenerationBudget
from test_data_agent.core.privacy import looks_sensitive_value
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_csv import compile_text_replacement_table, match_scoped_text
from test_data_agent.core.transformation_policy import (
    DropAction, PreserveAction, RejectUnmatched, ReplaceTextAction,
)
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.csv_profiler import _csv_reader_from_snapshot, validate_csv_headers
from test_data_agent.io.transformation_receipt import _canonical_request, verify_local_receipt


class TransformationExecutionError(ValueError):
    """Value-free replacement failure; no partial output is returned."""


def replace_csv_snapshot(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int,
    max_output_bytes: int, budget: GenerationBudget, receipt_path: Path | None = None,
) -> bytes:
    """Apply reviewed actions to fixed bytes; preservation needs a bound receipt."""
    try:
        if type(max_output_bytes) is not int or max_output_bytes < 1:
            raise ValueError
        limit = min(max_output_bytes, DEFAULT_MAX_INPUT_FILE_BYTES)
        canonical = _canonical_request(request, max_total_bytes=max_total_bytes,
                                       max_review_bytes=max_review_bytes, budget=budget)
        policy_bytes = next(part.payload for part in canonical.parts if part.kind == "policy")
        policy = load_behavior_policy_yaml(policy_bytes, max_bytes=max_total_bytes, budget=budget)
        source = next(part for part in canonical.parts if part.kind == "source")
        mappings = {part.name: part.payload for part in canonical.parts if part.kind == "mapping"}
        file_table = (compile_text_replacement_table(
            mappings[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        column_tables = {}
        dropped = set()
        needs_receipt = False
        actions = {decision.field: decision.behavior for decision in policy.fields}
        for decision in policy.fields:
            action = decision.behavior
            if decision.entity != source.name:
                raise ValueError
            if isinstance(action, DropAction):
                dropped.add(decision.field)
                continue
            if isinstance(action, PreserveAction):
                needs_receipt = True
                continue
            if (not isinstance(action, ReplaceTextAction)
                    or not isinstance(action.unmatched, (RejectUnmatched, PreserveAction))):
                raise ValueError
            needs_receipt |= isinstance(action.unmatched, PreserveAction)
            if action.mapping is not None:
                column_tables[decision.field] = compile_text_replacement_table(
                    mappings[action.mapping.path], action.mapping, budget=budget)
        if needs_receipt:
            if receipt_path is None:
                raise ValueError
            verify_local_receipt(canonical, receipt_path, max_total_bytes=max_total_bytes,
                                 max_review_bytes=max_review_bytes, budget=budget)
        reader = _csv_reader_from_snapshot(source.payload)
        names = tuple(validate_csv_headers(reader.fieldnames))
        if set(names) != {decision.field for decision in policy.fields}:
            raise ValueError
        reader.fieldnames = list(names)
        output_names = tuple(name for name in names if name not in dropped)
        output = io.BytesIO()

        def append_row(values: tuple[str, ...]) -> None:
            budget.check("CSV replacement output")
            row_buffer = io.StringIO(newline="")
            csv.writer(row_buffer, lineterminator="\n").writerow(values)
            encoded = row_buffer.getvalue().encode("utf-8")
            if output.tell() + len(encoded) > limit:
                raise ValueError
            output.write(encoded)

        if any(looks_sensitive_value(name) for name in output_names):
            raise ValueError
        append_row(output_names)
        for row in reader:
            budget.check("CSV replacement")
            if set(row) != set(names) or any(type(value) is not str for value in row.values()):
                raise ValueError
            values = []
            for name in output_names:
                budget.check("CSV replacement cell")
                action = actions[name]
                if isinstance(action, PreserveAction):
                    values.append(row[name])
                    continue
                match = match_scoped_text(row[name], name, file_table, column_tables)
                if match is not None:
                    values.append(match.replacement)
                elif isinstance(action, ReplaceTextAction) and isinstance(action.unmatched, PreserveAction):
                    values.append(row[name])
                else:
                    raise ValueError
            replaced = tuple(values)
            if output_names == names and replaced == tuple(row[name] for name in names):
                raise ValueError
            if any(looks_sensitive_value(value) for value in replaced):
                raise ValueError
            append_row(replaced)
        budget.check("CSV replacement")
        return output.getvalue()
    except (OSError, ValueError, TypeError, AttributeError, KeyError, StopIteration, csv.Error):
        pass
    try:
        raise TransformationExecutionError("invalid CSV replacement")
    except TransformationExecutionError as error:
        error.__context__ = None
        raise
