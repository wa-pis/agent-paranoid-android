"""Closed CSV replacement prototype; not wired to public execution surfaces.

Development/tests only pending end-to-end safety review and activation gates.
Preservation requires an existing local receipt. No filesystem publication,
receipt minting or external access.
"""

import csv
from decimal import Decimal
from datetime import date
from test_data_agent.io.transformation_input import source_reader, matching_text, same_native_value
import io
import math
from graphlib import TopologicalSorter
from dataclasses import dataclass, field, replace
from pathlib import Path
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
from test_data_agent.core.transformation_mapping import CsvMapping, DomainMapping, InlineMapping, validate_inline_scalar_mapping
from test_data_agent.core.transformation_policy import (
    DeriveAction, DropAction, PreserveAction, RejectUnmatched, ReplaceTextAction, SubstituteAction, SynthesizeAction,
)
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml, load_generation_policy_yaml
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation.reconciliation import assert_generated_dataset_valid
from test_data_agent.rules.expressions import eval_exact_decimal, eval_exact_integer, expression_constants, safe_eval
from test_data_agent.core.decimal_units import decimal_from_units, decimal_to_units
from test_data_agent.core.transformation_report import SourceRetentionSummary, retention_summary_from_counts
from test_data_agent.core.transformation_report import ProvenanceSummary, provenance_summary
from test_data_agent.csv_profiler import validate_csv_headers, parse_bool
from test_data_agent.io.transformation_receipt import _canonical_request, verify_local_receipt


class TransformationExecutionError(ValueError):
    """Value-free replacement failure; no partial output is returned."""


@dataclass(frozen=True, slots=True)
class CsvTransformationResult:
    """Restricted output bytes plus a value-free summary; not a public artifact."""

    csv_bytes: bytes = field(repr=False)
    retention: SourceRetentionSummary
    columns: tuple[str, ...] = field(repr=False)
    rows: tuple[tuple[str | None, ...], ...] = field(repr=False)
    provenance: ProvenanceSummary | None = None


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
        reader = source_reader(source, policy, budget=budget)
        names = tuple(validate_csv_headers(reader.fieldnames))
        reader.fieldnames = list(names)

        def events() -> Iterator[TextTraceEvent]:
            for row_number, row in enumerate(reader, 1):
                budget.check("CSV replacement trace")
                if set(row) != set(names) or any(type(value) is not str and not (policy.input_format == "parquet" and (value is None or type(value) in (int, float, bool, Decimal, date))) for value in row.values()):
                    raise ValueError
                for column_number, name in enumerate(names, 1):
                    budget.check("CSV replacement trace cell")
                    if isinstance(actions[name], ReplaceTextAction):
                        yield text_trace_event(row_number, column_number,
                            (match_scoped_text(matching_text(policy, name, row[name]), name, file_table, column_tables) if row[name] is not None else None))

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
        decimal_types = {decision.field: decision.decimal_type for decision in policy.fields
                         if decision.decimal_type is not None}
        source = next(part for part in canonical.parts if part.kind == "source")
        mappings = {part.name: part.payload for part in canonical.parts if part.kind == "mapping"}
        profile = DatasetProfile.model_validate_json(
            next(part.payload for part in canonical.parts if part.kind == "evidence"))
        field_types = {field.name: field.data_type for entity in profile.entities for field in entity.fields}
        field_nullable = {field.name: field.nullable for entity in profile.entities for field in entity.fields}
        field_types.update({name: FieldType.DECIMAL for name in decimal_types})

        def scalar(name: str, value: Any) -> Any:
            if policy.input_format == "parquet" and type(value) is date:
                return value.isoformat()
            if policy.input_format == "parquet" and field_types[name] == FieldType.BOOLEAN:
                if type(value) is bool:
                    return value
                parsed = parse_bool(value)
                if parsed is None:
                    raise ValueError
                return parsed
            if policy.input_format == "parquet" and type(value) in (int, float):
                return value
            if name in decimal_types:
                shape = decimal_types[name]
                units = decimal_to_units(format(value, "f") if isinstance(value, Decimal) else value,
                    precision=shape.precision, scale=shape.scale)
                return decimal_from_units(units, precision=shape.precision, scale=shape.scale)
            return normalize_csv_scalar(value, field_types[name])
        file_table = (compile_text_replacement_table(
            mappings[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        column_tables = {}
        substitutions: dict[str, dict[tuple[str | int | float | None, ...], str | None]] = {}
        substitution_columns: dict[str, tuple[str, ...]] = {}
        domains = {domain.name: domain.mapping for domain in policy.domains}
        dropped = set()
        needs_receipt = False
        actions = {decision.field: decision.behavior for decision in policy.fields}
        temporal_types = {decision.field: decision.temporal_type for decision in policy.fields
                          if decision.temporal_type is not None}
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
            if isinstance(action, DeriveAction):
                allowed = ((FieldType.INTEGER, FieldType.DECIMAL)
                           if decision.field in decimal_types else (FieldType.INTEGER, FieldType.FLOAT))
                if (field_types[decision.field] not in allowed or any(
                        field_types[name] not in allowed
                        for name in action.dependencies)):
                    raise ValueError
                if field_types[decision.field] == FieldType.INTEGER and any(
                        field_types[name] != FieldType.INTEGER for name in action.dependencies):
                    raise ValueError
                if any(type(value) not in (int, float) or not math.isfinite(value)
                       for value in expression_constants(action.expression)):
                    raise ValueError
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
                if field_types[decision.field] == FieldType.BOOLEAN and policy.input_format != "parquet":
                    raise ValueError
                if field_types[decision.field] not in (FieldType.STRING, FieldType.INTEGER, FieldType.FLOAT, FieldType.DATE, FieldType.DECIMAL, FieldType.BOOLEAN) or not isinstance(
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
                    if any(field_types[name] not in (FieldType.STRING, FieldType.INTEGER, FieldType.FLOAT, FieldType.DATE, FieldType.DECIMAL, FieldType.BOOLEAN) for name in source_columns):
                        raise ValueError
                    declaration = domains[declaration.name]
                shapes = tuple((decimal_types[name].precision, decimal_types[name].scale)
                               if name in decimal_types else None for name in source_columns)
                if isinstance(declaration, CsvMapping):
                    parsed = parse_csv_mapping_bytes(mappings[declaration.path], declaration, budget=budget)
                    declaration = normalize_csv_mapping(parsed,
                        data_types=tuple(field_types[name] for name in source_columns),
                        nullable=tuple(field_nullable[name] for name in source_columns), budget=budget, decimal_shapes=shapes)
                else:
                    declaration = validate_inline_scalar_mapping(declaration,
                        data_types=tuple(field_types[name] for name in source_columns),
                        nullable=tuple(field_nullable[name] for name in source_columns), decimal_shapes=shapes)
                if not isinstance(declaration, InlineMapping):
                    raise ValueError
                pairs: dict[tuple[str | int | float | None, ...], str | None] = {}
                for entry in declaration.entries:
                    budget.check("CSV substitution")
                    if any(value is not None and type(value) not in (str, int, float, bool)
                           for value in (*entry.original, *entry.replacement)):
                        raise ValueError
                    if (None in entry.original and policy.csv_nulls.input_token is None and policy.input_format == "csv"
                            or None in entry.replacement and policy.csv_nulls.output_token is None and policy.output is None):
                        raise ValueError
                    replacement = entry.replacement[component]
                    pairs[entry.original] = (
                        None if replacement is None else str(replacement))
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
        reader = source_reader(source, policy, budget=budget)
        names = tuple(validate_csv_headers(reader.fieldnames))
        if set(names) != {decision.field for decision in policy.fields}:
            raise ValueError
        reader.fieldnames = list(names)
        output_names = tuple(name for name in names if name not in dropped)
        execution_names = tuple(TopologicalSorter({
            name: set(action.dependencies) if isinstance(action := actions[name], DeriveAction) else set()
            for name in output_names
        }).static_order())
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
        def preserved(name: str, original: str, action: PreserveAction) -> str:
            origins[name] = "replacement" if action.format_temporal else "original"
            if policy.output is not None:
                target = next(item for item in policy.output.fields if item.name == name)
                if target.type != field_types[name].value or target.temporal_type is not None:
                    origins[name] = "replacement"
            if original == policy.csv_nulls.input_token:
                if policy.csv_nulls.output_token is None and policy.output is None:
                    raise ValueError
                null_fields.add(name)
                return policy.csv_nulls.output_token or ""
            return temporal_types[name].render(original) if action.format_temporal else original

        def synthesized(action: SynthesizeAction, row_index: int, name: str, original: str) -> str:
            origins[name] = "synthetic"
            value = generated[action.generation_policy_ref][row_index][name]
            if value is None:
                if policy.csv_nulls.output_token is None and policy.output is None:
                    raise ValueError
                null_fields.add(name)
                return policy.csv_nulls.output_token or ""
            rendered = str(value)
            if original != policy.csv_nulls.input_token and scalar(name, rendered) == scalar(name, original):
                # Owner-approved numeric zero coincidence: generation already ran.
                # Never applies to text/bool, mappings, preservation or whole rows.
                if (field_types[name] not in {FieldType.INTEGER, FieldType.FLOAT, FieldType.DECIMAL}
                        or scalar(name, rendered) != 0):
                    raise ValueError
                coincident_zero_fields.add(name)
            return rendered

        unchanged = compared = dropped_cells = 0
        origin_counts = {"replacement": 0, "synthetic": 0, "original": 0}
        logical_rows: list[tuple[str | None, ...]] = []
        for row_index, row in enumerate(reader):
            origins = dict.fromkeys(execution_names, "replacement")
            null_fields: set[str] = set()
            coincident_zero_fields: set[str] = set()
            budget.check("CSV replacement")
            if set(row) != set(names) or any(type(value) is not str and not (policy.input_format == "parquet" and (value is None or type(value) in (int, float, bool, Decimal, date))) for value in row.values()):
                raise ValueError
            for name in decimal_types:
                if row[name] != policy.csv_nulls.input_token:
                    scalar(name, row[name])
            values: list[str] = []
            preserved_fields: set[str] = set()
            for name in execution_names:
                budget.check("CSV replacement cell")
                action = actions[name]
                if isinstance(action, DeriveAction):
                    if null_fields.intersection(action.dependencies):
                        raise ValueError
                    transformed = dict(zip(execution_names, values))
                    operands = {
                        dependency: scalar(dependency, transformed[dependency])
                        for dependency in action.dependencies}
                    if name in decimal_types:
                        shape = decimal_types[name]
                        values.append(format(eval_exact_decimal(action.expression, operands,
                            precision=shape.precision, scale=shape.scale, budget=budget), "f"))
                        continue
                    if field_types[name] == FieldType.INTEGER:
                        values.append(str(eval_exact_integer(action.expression, operands, budget=budget)))
                        continue
                    result = safe_eval(action.expression, operands)
                    if type(result) not in (int, float) or not math.isfinite(result):
                        raise ValueError
                    values.append(str(float(result)))
                    continue
                if isinstance(action, PreserveAction):
                    preserved_fields.add(name)
                    values.append(preserved(name, row[name], action))
                    continue
                if isinstance(action, SynthesizeAction):
                    values.append(synthesized(action, row_index, name, row[name]))
                    continue
                if isinstance(action, SubstituteAction):
                    key = tuple(None if row[column] == policy.csv_nulls.input_token else
                                format(scalar(column, row[column]), "f") if column in decimal_types
                                else scalar(column, row[column])
                                for column in substitution_columns[name])
                    if key in substitutions[name]:
                        replacement = substitutions[name][key]
                        if replacement is None:
                            if policy.csv_nulls.output_token is None and policy.output is None:
                                raise ValueError
                            null_fields.add(name)
                            replacement = policy.csv_nulls.output_token or ""
                        values.append(replacement)
                    elif isinstance(action.unmatched, PreserveAction):
                        preserved_fields.add(name)
                        values.append(preserved(name, row[name], action.unmatched))
                    elif isinstance(action.unmatched, SynthesizeAction):
                        values.append(synthesized(action.unmatched, row_index, name, row[name]))
                    else:
                        raise ValueError
                    continue
                match = (match_scoped_text(matching_text(policy, name, row[name]), name, file_table, column_tables) if row[name] is not None else None)
                if match is not None:
                    values.append(match.replacement)
                elif isinstance(action, ReplaceTextAction) and isinstance(action.unmatched, PreserveAction):
                    preserved_fields.add(name)
                    values.append(preserved(name, row[name], action.unmatched))
                elif isinstance(action, ReplaceTextAction) and isinstance(action.unmatched, SynthesizeAction):
                    values.append(synthesized(action.unmatched, row_index, name, row[name]))
                else:
                    raise ValueError
            transformed = dict(zip(execution_names, values, strict=True))
            replaced = tuple(transformed[name] for name in output_names)
            if policy.output is None and policy.csv_nulls.output_token is not None and any(
                    value == policy.csv_nulls.output_token and name not in null_fields
                    for name, value in zip(output_names, replaced, strict=True)):
                raise ValueError
            for name in decimal_types:
                if name in transformed and name not in null_fields:
                    scalar(name, transformed[name])
            if output_names == names and (tuple(None if name in null_fields else
                    row[name] if name in coincident_zero_fields else value
                    for name, value in zip(output_names, replaced, strict=True))
                    == tuple(None if row[name] == policy.csv_nulls.input_token else row[name] for name in names)
                    or preserved_fields == set(names)):
                raise ValueError
            if policy.input_format == "parquet" and output_names == names and all(
                    same_native_value(row[name], None if name in null_fields else value)
                    for name, value in zip(output_names, replaced, strict=True)):
                raise ValueError
            if any(looks_sensitive_value(value) for value in replaced):
                raise ValueError
            append_row(replaced)
            final_row = {name: None if name in null_fields else value
                         for name, value in zip(output_names, replaced, strict=True)}
            logical_rows.append(tuple(final_row[name] for name in output_names))
            for name in output_names:
                origin_counts[origins[name]] += 1
            for reference, spec in generation_specs.items():
                final_generated[reference].append({field.name: final_row[field.name]
                                                   for field in spec.entities[0].fields})
            compared += len(output_names)
            dropped_cells += len(dropped)
            for name, value in zip(output_names, replaced, strict=True):
                if name in null_fields:
                    unchanged += int(row[name] == policy.csv_nulls.input_token)
                    continue
                if row[name] == policy.csv_nulls.input_token:
                    continue
                try:
                    same = scalar(name, row[name]) == scalar(name, value)
                except ValueError:
                    # Unconditional text replacement may change a numeric field to text.
                    same = row[name] == value
                unchanged += int(same)
        budget.check("CSV replacement")
        for reference, spec in generation_specs.items():
            assert_generated_dataset_valid({source.name: final_generated[reference]}, spec)
            budget.check("CSV synthesis final validation")
        retention = retention_summary_from_counts(unchanged, compared, dropped_cells)
        if policy.output is not None or any(
                isinstance(action, PreserveAction) and action.format_temporal for action in actions.values()):
            # A lexical comparison does not measure final typed/temporal output equality.
            retention = replace(retention, status="unavailable", unchanged_cells=None, unchanged_percent=None)
        provenance = provenance_summary(origin_counts["replacement"], origin_counts["synthetic"],
                                        origin_counts["original"], dropped_cells)
        return CsvTransformationResult(output.getvalue(), retention, output_names, tuple(logical_rows), provenance)
    except (OSError, ValueError, TypeError, ArithmeticError, AttributeError, KeyError, IndexError, StopIteration, csv.Error):
        pass
    try:
        raise TransformationExecutionError("invalid CSV replacement")
    except TransformationExecutionError as error:
        error.__context__ = None
        raise
