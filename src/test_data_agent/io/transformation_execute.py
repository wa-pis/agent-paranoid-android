"""Closed CSV replacement prototype; not wired to public execution surfaces.

Development/tests only pending end-to-end safety review and activation gates.
Preservation requires an existing local receipt. No filesystem publication,
receipt minting or external access.
"""

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast
from typing import Any
from collections.abc import Iterator

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_FILE_BYTES, GenerationBudget
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.settings import GenerationMode
from test_data_agent.core.field import FieldType
from test_data_agent.core.privacy import looks_sensitive_value
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_csv import (
    compile_text_replacement_table, match_scoped_text, normalize_csv_mapping,
    normalize_csv_scalar, parse_csv_mapping_bytes,
    summarize_text_trace, text_trace_event, TextTraceEvent, TextTraceSummary,
)
from test_data_agent.core.transformation_mapping import CsvMapping, DomainMapping, InlineMapping
from test_data_agent.core.transformation_policy import (
    DropAction, PreserveAction, RejectUnmatched, ReplaceTextAction, SubstituteAction, SynthesizeAction,
)
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml, load_generation_policy_yaml
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation.reconciliation import assert_generated_dataset_valid
from test_data_agent.core.transformation_report import SourceRetentionSummary, retention_summary_from_counts
from test_data_agent.csv_profiler import _csv_reader_from_snapshot, validate_csv_headers
from test_data_agent.io.transformation_receipt import _canonical_request, verify_local_receipt


class TransformationExecutionError(ValueError):
    """Value-free replacement failure; no partial output is returned."""


@dataclass(frozen=True, slots=True)
class CsvTransformationResult:
    """Restricted output bytes plus a value-free summary; not a public artifact."""

    csv_bytes: bytes = field(repr=False)
    retention: SourceRetentionSummary


def trace_csv_replacements(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int,
    max_events: int, max_cells: int, max_rule_counts: int, budget: GenerationBudget,
) -> TextTraceSummary:
    """Private local dry-run of replace rules; never return cells or execute actions."""
    try:
        canonical = _canonical_request(request, max_total_bytes=max_total_bytes,
                                       max_review_bytes=max_review_bytes, budget=budget)
        policy = load_behavior_policy_yaml(
            next(part.payload for part in canonical.parts if part.kind == "policy"),
            max_bytes=max_total_bytes, budget=budget)
        source = next(part for part in canonical.parts if part.kind == "source")
        mappings = {part.name: part.payload for part in canonical.parts if part.kind == "mapping"}
        file_table = (compile_text_replacement_table(
            mappings[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        actions = {item.field: item.behavior for item in policy.fields}
        column_tables = {
            name: compile_text_replacement_table(mappings[action.mapping.path], action.mapping, budget=budget)
            for name, action in actions.items()
            if isinstance(action, ReplaceTextAction) and action.mapping is not None
        }
        reader = _csv_reader_from_snapshot(source.payload)
        names = tuple(validate_csv_headers(reader.fieldnames))
        reader.fieldnames = list(names)

        def events() -> Iterator[TextTraceEvent]:
            for row_number, row in enumerate(reader, 1):
                budget.check("CSV replacement trace")
                if set(row) != set(names) or any(type(value) is not str for value in row.values()):
                    raise ValueError
                for column_number, name in enumerate(names, 1):
                    budget.check("CSV replacement trace cell")
                    if isinstance(actions[name], ReplaceTextAction):
                        yield text_trace_event(row_number, column_number,
                            match_scoped_text(row[name], name, file_table, column_tables))

        return summarize_text_trace(events(), max_events=max_events, max_cells=max_cells,
                                    max_rule_counts=max_rule_counts, budget=budget)
    except (OSError, ValueError, TypeError, AttributeError, KeyError, StopIteration, csv.Error):
        pass
    try:
        raise TransformationExecutionError("invalid CSV replacement trace")
    except TransformationExecutionError as error:
        error.__context__ = None
        raise


def replace_csv_snapshot(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int,
    max_output_bytes: int, budget: GenerationBudget, receipt_path: Path | None = None,
) -> CsvTransformationResult:
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
        profile = DatasetProfile.model_validate_json(
            next(part.payload for part in canonical.parts if part.kind == "evidence"))
        field_types = {field.name: field.data_type for entity in profile.entities for field in entity.fields}
        file_table = (compile_text_replacement_table(
            mappings[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        column_tables = {}
        substitutions: dict[str, dict[tuple[str | int | float, ...], str]] = {}
        substitution_columns: dict[str, tuple[str, ...]] = {}
        domains = {domain.name: domain.mapping for domain in policy.domains}
        dropped = set()
        needs_receipt = False
        actions = {decision.field: decision.behavior for decision in policy.fields}
        generation_specs: dict[str, DatasetSpec] = {}
        generated: dict[str, list[dict[str, Any]]] = {}
        final_generated: dict[str, list[dict[str, Any]]] = {}
        generation_bytes = {part.name: part.payload for part in canonical.parts if part.kind == "generation_policy"}
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
            synthesis = (action if isinstance(action, SynthesizeAction) else
                         action.unmatched if isinstance(action, (ReplaceTextAction, SubstituteAction)) else None)
            if isinstance(synthesis, SynthesizeAction):
                reference = synthesis.generation_policy_ref
                if reference not in generation_specs:
                    spec = load_generation_policy_yaml(generation_bytes[reference],
                        max_bytes=max_total_bytes, budget=budget)
                    if (len(spec.entities) != 1 or spec.entities[0].name != source.name
                            or spec.generation_settings.mode != GenerationMode.VALID):
                        raise ValueError
                    spec.entities[0].row_count = next(entity.row_count for entity in profile.entities
                                                     if entity.name == source.name)
                    if any(field.name not in actions or isinstance(actions[field.name], DropAction)
                           for field in spec.entities[0].fields):
                        raise ValueError
                    generation_specs[reference] = spec
                    generated[reference] = generate_dataset(spec, policy.seed, budget=budget)[source.name]
                    final_generated[reference] = []
            if isinstance(action, SynthesizeAction):
                continue
            if isinstance(action, SubstituteAction):
                if field_types[decision.field] not in (FieldType.STRING, FieldType.INTEGER, FieldType.FLOAT, FieldType.DATE) or not isinstance(
                        action.unmatched, (RejectUnmatched, PreserveAction, SynthesizeAction)):
                    raise ValueError
                needs_receipt |= isinstance(action.unmatched, PreserveAction)
                declaration = action.mapping
                component = 0
                source_columns: tuple[str, ...] = (decision.field,)
                if isinstance(declaration, DomainMapping):
                    component = declaration.component or 0
                    members = sorted(
                        (item.behavior.mapping.component or 0, item.field)
                        for item in policy.fields if isinstance(item.behavior, SubstituteAction)
                        and isinstance(item.behavior.mapping, DomainMapping)
                        and item.behavior.mapping.name == declaration.name)
                    source_columns = tuple(name for _, name in members)
                    if any(field_types[name] not in (FieldType.STRING, FieldType.INTEGER, FieldType.FLOAT, FieldType.DATE) for name in source_columns):
                        raise ValueError
                    declaration = domains[declaration.name]
                if isinstance(declaration, CsvMapping):
                    parsed = parse_csv_mapping_bytes(mappings[declaration.path], declaration, budget=budget)
                    declaration = normalize_csv_mapping(parsed,
                        data_types=tuple(field_types[name] for name in source_columns),
                        nullable=tuple(False for _ in source_columns), budget=budget)
                if not isinstance(declaration, InlineMapping):
                    raise ValueError
                pairs: dict[tuple[str | int | float, ...], str] = {}
                for entry in declaration.entries:
                    budget.check("CSV substitution")
                    if any(type(value) not in (str, int, float) for value in (*entry.original, *entry.replacement)):
                        raise ValueError
                    pairs[cast(tuple[str | int | float, ...], entry.original)] = str(entry.replacement[component])
                substitutions[decision.field] = pairs
                substitution_columns[decision.field] = source_columns
                continue
            if (not isinstance(action, ReplaceTextAction)
                    or not isinstance(action.unmatched, (RejectUnmatched, PreserveAction, SynthesizeAction))):
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
        def synthesized(action: SynthesizeAction, row_index: int, name: str, original: str) -> str:
            value = generated[action.generation_policy_ref][row_index][name]
            if value is None:
                raise ValueError  # CSV null encoding remains an explicit pending contract.
            rendered = str(value)
            if normalize_csv_scalar(rendered, field_types[name]) == normalize_csv_scalar(original, field_types[name]):
                raise ValueError
            return rendered

        unchanged = compared = dropped_cells = 0
        for row_index, row in enumerate(reader):
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
                if isinstance(action, SynthesizeAction):
                    values.append(synthesized(action, row_index, name, row[name]))
                    continue
                if isinstance(action, SubstituteAction):
                    key = tuple(normalize_csv_scalar(row[column], field_types[column])
                                for column in substitution_columns[name])
                    if key in substitutions[name]:
                        values.append(substitutions[name][key])
                    elif isinstance(action.unmatched, PreserveAction):
                        values.append(row[name])
                    elif isinstance(action.unmatched, SynthesizeAction):
                        values.append(synthesized(action.unmatched, row_index, name, row[name]))
                    else:
                        raise ValueError
                    continue
                match = match_scoped_text(row[name], name, file_table, column_tables)
                if match is not None:
                    values.append(match.replacement)
                elif isinstance(action, ReplaceTextAction) and isinstance(action.unmatched, PreserveAction):
                    values.append(row[name])
                elif isinstance(action, ReplaceTextAction) and isinstance(action.unmatched, SynthesizeAction):
                    values.append(synthesized(action.unmatched, row_index, name, row[name]))
                else:
                    raise ValueError
            replaced = tuple(values)
            if output_names == names and replaced == tuple(row[name] for name in names):
                raise ValueError
            if any(looks_sensitive_value(value) for value in replaced):
                raise ValueError
            append_row(replaced)
            final_row = dict(zip(output_names, replaced, strict=True))
            for reference, spec in generation_specs.items():
                final_generated[reference].append({field.name: final_row[field.name]
                                                   for field in spec.entities[0].fields})
            compared += len(output_names)
            dropped_cells += len(dropped)
            unchanged += sum(row[name] == value for name, value in zip(output_names, replaced, strict=True))
        budget.check("CSV replacement")
        for reference, spec in generation_specs.items():
            assert_generated_dataset_valid({source.name: final_generated[reference]}, spec)
            budget.check("CSV synthesis final validation")
        return CsvTransformationResult(
            output.getvalue(), retention_summary_from_counts(unchanged, compared, dropped_cells))
    except (OSError, ValueError, TypeError, AttributeError, KeyError, IndexError, StopIteration, csv.Error):
        pass
    try:
        raise TransformationExecutionError("invalid CSV replacement")
    except TransformationExecutionError as error:
        error.__context__ = None
        raise
