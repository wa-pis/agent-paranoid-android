"""Private fixed CSV source snapshots; not transformation authorization."""

import csv
import os
from collections.abc import Iterator, Sequence
from pathlib import Path

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_CELLS, DEFAULT_MAX_INPUT_COLUMNS, DEFAULT_MAX_INPUT_FILE_BYTES,
    GenerationBudget,
)
from test_data_agent.core.privacy import is_sensitive_field
from test_data_agent.core.transformation_csv import (
    TextTraceEvent, TextTraceSummary, compile_text_replacement_table, match_scoped_text,
    summarize_text_trace, text_trace_event,
)
from test_data_agent.core.transformation_approval import ApprovalRequest, prepare_approval_request
from test_data_agent.core.transformation_mapping import CsvMapping
from test_data_agent.core.transformation_policy import ReplaceTextAction, SubstituteAction, SynthesizeAction
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.csv_profiler import _csv_reader_from_snapshot, profile_csv_bytes, validate_csv_headers
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
from test_data_agent.io.path_policy import open_regular_file


class TransformationSourceError(ValueError):
    """Invalid source snapshot or stale profile; never echo source values."""


def prepare_csv_review_request(
    policy_yaml: bytes, source: SnapshotPart, referenced_parts: Sequence[SnapshotPart], *,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    """Derive review evidence from the same fixed CSV bytes bound to approval."""
    try:
        budget.check("transformation source review")
        if (not isinstance(source, SnapshotPart) or source.kind != "source"
                or type(source.name) is not str or not source.name
                or type(source.payload) is not bytes
                or len(referenced_parts) > 3 * DEFAULT_MAX_INPUT_COLUMNS
                or any(not isinstance(part, SnapshotPart)
                       or part.kind not in {"mapping", "generation_policy"}
                       for part in referenced_parts)):
            raise ValueError
        profile = csv_profile_to_dataset_profile(profile_csv_bytes(
            source.payload, source.name, budget=budget,
            max_bytes=min(DEFAULT_MAX_INPUT_FILE_BYTES, max_total_bytes),
        ))
        evidence_json = profile.model_dump_json().encode("utf-8")
        request = prepare_approval_request(
            policy_yaml, evidence_json, (source, *referenced_parts),
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
        )
        reject_sensitive_text_reuse(policy_yaml, profile, source, referenced_parts, budget=budget)
        return request
    except (OSError, ValueError, TypeError, AttributeError, csv.Error):
        raise TransformationSourceError("invalid transformation source review") from None


def prepare_csv_review_from_paths(
    source_path: Path, table_name: str, policy_root: Path, policy_path: str, *,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    """Read private inputs once and prepare a value-free local CSV review."""
    try:
        if type(max_total_bytes) is not int or max_total_bytes < 1:
            raise ValueError
        policy_yaml = read_mapping_snapshot(
            policy_root, policy_path, max_bytes=max_total_bytes, budget=budget,
        ).payload
        remaining = max_total_bytes - len(policy_yaml)
        policy = load_behavior_policy_yaml(policy_yaml, max_bytes=max_total_bytes, budget=budget)
        mapping_paths = {domain.mapping.path for domain in policy.domains
                         if isinstance(domain.mapping, CsvMapping)}
        if policy.file_text_mapping is not None:
            mapping_paths.add(policy.file_text_mapping.path)
        generation_paths: set[str] = set()
        for decision in policy.fields:
            action = decision.behavior
            if isinstance(action, SynthesizeAction):
                generation_paths.add(action.generation_policy_ref)
            elif isinstance(action, SubstituteAction):
                if isinstance(action.mapping, CsvMapping):
                    mapping_paths.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_paths.add(action.unmatched.generation_policy_ref)
            elif isinstance(action, ReplaceTextAction):
                if action.mapping is not None:
                    mapping_paths.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_paths.add(action.unmatched.generation_policy_ref)
        if len(mapping_paths) + len(generation_paths) > 3 * DEFAULT_MAX_INPUT_COLUMNS:
            raise ValueError
        referenced_parts: list[SnapshotPart] = []
        for kind, paths in (("mapping", mapping_paths), ("generation_policy", generation_paths)):
            for path in sorted(paths):
                snapshot = read_mapping_snapshot(
                    policy_root, path, max_bytes=remaining, budget=budget,
                )
                remaining -= len(snapshot.payload)
                referenced_parts.append(SnapshotPart(kind, path, snapshot.payload))
        source = load_csv_source_snapshot(
            source_path, table_name, budget=budget,
            max_bytes=min(DEFAULT_MAX_INPUT_FILE_BYTES, remaining),
        )
        return prepare_csv_review_request(
            policy_yaml, source, tuple(referenced_parts), max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget,
        )
    except (OSError, ValueError, TypeError, AttributeError):
        raise TransformationSourceError("invalid transformation source review") from None


def trace_csv_review_request(
    request: ApprovalRequest, *, max_events: int, max_cells: int,
    budget: GenerationBudget,
) -> TextTraceSummary:
    """Trace replacement matches from reviewed bytes, without exposing values."""
    try:
        parts = {(part.kind, part.name): part.payload for part in request.parts}
        policy_yaml = parts[("policy", "behavior.yaml")]
        policy = load_behavior_policy_yaml(policy_yaml, max_bytes=len(policy_yaml), budget=budget)
        source_parts = [part for part in request.parts if part.kind == "source"]
        if len(source_parts) != 1 or len(parts) != len(request.parts):
            raise ValueError
        source = source_parts[0]
        mapping_bytes = {part.name: part.payload for part in request.parts if part.kind == "mapping"}
        file_table = (compile_text_replacement_table(
            mapping_bytes[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        column_tables = {}
        selected = set()
        for decision in policy.fields:
            if decision.entity != source.name:
                raise ValueError
            if isinstance(decision.behavior, ReplaceTextAction):
                selected.add(decision.field)
                if decision.behavior.mapping is not None:
                    column_tables[decision.field] = compile_text_replacement_table(
                        mapping_bytes[decision.behavior.mapping.path], decision.behavior.mapping,
                        budget=budget,
                    )
        reader = _csv_reader_from_snapshot(source.payload)
        names = validate_csv_headers(reader.fieldnames)
        if set(names) != {decision.field for decision in policy.fields}:
            raise ValueError
        reader.fieldnames = names

        def events() -> Iterator[TextTraceEvent]:
            for row_ordinal, row in enumerate(reader, start=1):
                budget.check("text trace")
                if set(row) != set(names) or any(type(value) is not str for value in row.values()):
                    raise ValueError
                for column_ordinal, column in enumerate(names, start=1):
                    if column in selected:
                        match = match_scoped_text(row[column], column, file_table, column_tables)
                        yield text_trace_event(row_ordinal, column_ordinal, match)

        return summarize_text_trace(
            events(), max_events=max_events, max_cells=min(max_cells, DEFAULT_MAX_INPUT_CELLS),
            max_rule_counts=DEFAULT_MAX_INPUT_COLUMNS * 2, budget=budget,
        )
    except (OSError, ValueError, TypeError, AttributeError, KeyError, csv.Error):
        raise TransformationSourceError("invalid transformation trace") from None


def reject_sensitive_text_reuse(
    policy_yaml: bytes, profile: DatasetProfile, source: SnapshotPart,
    referenced_parts: Sequence[SnapshotPart], *, budget: GenerationBudget,
) -> None:
    """Reject reachable sensitive replacements found in the fixed source bytes."""
    try:
        policy = load_behavior_policy_yaml(policy_yaml, max_bytes=len(policy_yaml), budget=budget)
        decisions = [item for item in policy.fields if isinstance(item.behavior, ReplaceTextAction)]
        if not decisions:
            return
        if any(item.entity != source.name for item in decisions):
            raise ValueError
        fields = {field.name: field for entity in profile.entities if entity.name == source.name
                  for field in entity.fields}
        declarations = {(item.entity, item.field): item for item in policy.fields}
        sensitive_source_columns = {name for name, field in fields.items() if (
            declarations[(source.name, name)].sensitivity != "non_sensitive" or field.sensitive
            or is_sensitive_field(field.name, field.semantic_type)
        )}
        sensitive = [item for item in decisions if (
            item.field in sensitive_source_columns
        )]
        if not sensitive:
            return
        mapping_bytes = {part.name: part.payload for part in referenced_parts if part.kind == "mapping"}
        file_table = (compile_text_replacement_table(
            mapping_bytes[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
        ) if policy.file_text_mapping is not None else None)
        column_tables = {}
        for item in sensitive:
            action = item.behavior
            if isinstance(action, ReplaceTextAction) and action.mapping is not None:
                column_tables[item.field] = compile_text_replacement_table(
                    mapping_bytes[action.mapping.path], action.mapping, budget=budget,
                )
        names = tuple(fields)
        active: dict[str, set[str]] = {item.field: set() for item in sensitive}
        reader = _csv_reader_from_snapshot(source.payload)
        normalized = validate_csv_headers(reader.fieldnames)
        if tuple(normalized) != names:
            raise ValueError
        reader.fieldnames = normalized
        for row in reader:
            budget.check("sensitive text replacement")
            if set(row) != set(names) or any(type(value) is not str for value in row.values()):
                raise ValueError
            for item in sensitive:
                match = match_scoped_text(row[item.field], item.field, file_table, column_tables)
                if match is not None:
                    active[item.field].add(match.replacement)
        if not any(active.values()):
            return
        active_replacements = {value for replacements in active.values() for value in replacements}
        reader = _csv_reader_from_snapshot(source.payload)
        normalized = validate_csv_headers(reader.fieldnames)
        if tuple(normalized) != names:
            raise ValueError
        reader.fieldnames = normalized
        for row in reader:
            budget.check("sensitive text replacement")
            if set(row) != set(names) or any(type(value) is not str for value in row.values()):
                raise ValueError
            if any(row[field] in active_replacements for field in sensitive_source_columns):
                raise ValueError
    except (OSError, ValueError, TypeError, AttributeError, csv.Error, KeyError):
        raise TransformationSourceError("invalid sensitive text replacement") from None


def load_csv_source_snapshot(
    path: Path, table_name: str, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
) -> SnapshotPart:
    """Read one regular file once; callers must reuse returned bytes."""
    try:
        budget.check("transformation source snapshot")
        if type(table_name) is not str or not table_name or type(max_bytes) is not int or max_bytes < 1:
            raise ValueError
        with open_regular_file(path) as handle:
            if os.fstat(handle.fileno()).st_size > max_bytes:
                raise ValueError
            payload = handle.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError
        budget.check("transformation source snapshot")
        return SnapshotPart("source", table_name, payload)
    except (OSError, ValueError, TypeError, AttributeError):
        raise TransformationSourceError("invalid transformation source") from None


def revalidate_csv_evidence(
    source: SnapshotPart, evidence_json: bytes, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
) -> DatasetProfile:
    """Reprofile fixed bytes and reject changed classification/evidence."""
    try:
        budget.check("transformation source evidence")
        if not isinstance(source, SnapshotPart) or source.kind != "source" or type(evidence_json) is not bytes:
            raise ValueError
        reviewed = DatasetProfile.model_validate_json(evidence_json)
        observed = csv_profile_to_dataset_profile(
            profile_csv_bytes(source.payload, source.name, budget=budget, max_bytes=max_bytes)
        )
        if reviewed.model_dump(mode="json") != observed.model_dump(mode="json"):
            raise ValueError
        budget.check("transformation source evidence")
        return observed
    except (OSError, ValueError, TypeError, AttributeError, csv.Error):
        raise TransformationSourceError("invalid transformation source evidence") from None
