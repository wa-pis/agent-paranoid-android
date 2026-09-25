"""Private CSV mapping parser."""

import csv
import io
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_CELL_CHARS, DEFAULT_MAX_INPUT_CELLS,
    DEFAULT_MAX_INPUT_FILE_BYTES, DEFAULT_MAX_INPUT_ROWS, DEFAULT_MAX_INPUT_COLUMNS,
    GenerationBudget,
)
from test_data_agent.core.transformation_mapping import (
    CsvMapping, InlineMapping, MappingDeclarationError, parse_mapping_declaration,
    validate_inline_mapping_shape, validate_inline_scalar_mapping,
)


@dataclass(frozen=True, slots=True, repr=False)
class TextReplacementTable:
    """Private exact-text lookup; no source-row fallback or execution authority."""

    _by_source: Mapping[str, tuple[str, int]] = field(repr=False)

    def lookup(self, value: str) -> tuple[str, int] | None:
        if type(value) is not str:
            raise MappingDeclarationError("invalid text replacement lookup") from None
        return self._by_source.get(value)


@dataclass(frozen=True, slots=True)
class TextMatch:
    replacement: str = field(repr=False)
    scope: Literal["file", "column"]
    rule_ordinal: int


@dataclass(frozen=True, slots=True)
class TextTraceEvent:
    row_ordinal: int
    column_ordinal: int
    matched: bool
    scope: Literal["file", "column"] | None
    rule_ordinal: int | None


@dataclass(frozen=True, slots=True)
class TextTraceSummary:
    events: tuple[TextTraceEvent, ...]
    matched_cells: int
    unmatched_cells: int
    rule_counts: tuple[tuple[int, Literal["file", "column"], int, int], ...]
    truncated: bool


def summarize_text_trace(
    events: Iterable[TextTraceEvent], *, max_events: int, max_cells: int,
    max_rule_counts: int, budget: GenerationBudget,
) -> TextTraceSummary:
    """Summarize bounded, value-free local match events only."""
    if (type(max_events) is not int or max_events < 1 or type(max_cells) is not int
            or max_cells < 1 or type(max_rule_counts) is not int or max_rule_counts < 1):
        raise MappingDeclarationError("invalid text trace limits") from None
    shown: list[TextTraceEvent] = []
    counts: dict[tuple[int, Literal["file", "column"], int], int] = {}
    matched = unmatched = total = 0
    for event in events:
        budget.check("text trace")
        if (not isinstance(event, TextTraceEvent) or total >= max_cells
                or type(event.row_ordinal) is not int or event.row_ordinal < 1
                or type(event.column_ordinal) is not int or event.column_ordinal < 1
                or type(event.matched) is not bool):
            raise MappingDeclarationError("invalid text trace event") from None
        total += 1
        if len(shown) < max_events:
            shown.append(event)
        if event.matched:
            if (event.scope not in ("file", "column")
                    or type(event.rule_ordinal) is not int or event.rule_ordinal < 1):
                raise MappingDeclarationError("invalid text trace event") from None
            key = (event.column_ordinal, event.scope, event.rule_ordinal)
            if key not in counts and len(counts) >= max_rule_counts:
                raise MappingDeclarationError("text trace rule limit exceeded") from None
            counts[key] = counts.get(key, 0) + 1
            matched += 1
        else:
            if event.scope is not None or event.rule_ordinal is not None:
                raise MappingDeclarationError("invalid text trace event") from None
            unmatched += 1
    budget.check("text trace")
    return TextTraceSummary(tuple(shown), matched, unmatched,
                            tuple((*key, count) for key, count in sorted(counts.items())),
                            total > max_events)


def text_trace_event(row_ordinal: int, column_ordinal: int, match: TextMatch | None) -> TextTraceEvent:
    """Build value-free local trace metadata from a private match result."""
    if (type(row_ordinal) is not int or row_ordinal < 1 or type(column_ordinal) is not int
            or column_ordinal < 1 or (match is not None and not isinstance(match, TextMatch))):
        raise MappingDeclarationError("invalid text trace event") from None
    return TextTraceEvent(row_ordinal, column_ordinal, match is not None,
                          match.scope if match is not None else None,
                          match.rule_ordinal if match is not None else None)


def match_scoped_text(
    value: str, column: str, file_table: TextReplacementTable | None,
    column_tables: Mapping[str, TextReplacementTable],
) -> TextMatch | None:
    """Match original text once, preferring a column rule over a file rule."""
    if type(value) is not str or type(column) is not str or not isinstance(column_tables, Mapping):
        raise MappingDeclarationError("invalid text replacement lookup") from None
    local_table = column_tables.get(column)
    if local_table is not None and not isinstance(local_table, TextReplacementTable):
        raise MappingDeclarationError("invalid text replacement lookup") from None
    if file_table is not None and not isinstance(file_table, TextReplacementTable):
        raise MappingDeclarationError("invalid text replacement lookup") from None
    local = local_table.lookup(value) if local_table is not None else None
    global_match = file_table.lookup(value) if file_table is not None else None
    if local is not None:
        return TextMatch(local[0], "column", local[1])
    if global_match is not None:
        return TextMatch(global_match[0], "file", global_match[1])
    return None


def match_text_row(
    values: tuple[str, ...], columns: tuple[str, ...],
    file_table: TextReplacementTable | None,
    column_tables: Mapping[str, TextReplacementTable],
) -> tuple[TextMatch | None, ...]:
    """Match one row once for replacement and value-free tracing."""
    if (type(values) is not tuple or type(columns) is not tuple or not values
            or len(values) != len(columns)
            or any(type(column) is not str or not column for column in columns)
            or len(set(columns)) != len(columns)):
        raise MappingDeclarationError("invalid text replacement row") from None
    return tuple(match_scoped_text(value, column, file_table, column_tables)
                 for column, value in zip(columns, values, strict=True))


def replace_text_row(
    values: tuple[str, ...], columns: tuple[str, ...],
    file_table: TextReplacementTable | None,
    column_tables: Mapping[str, TextReplacementTable],
) -> tuple[str, ...]:
    """Apply explicit text rules once; reject any uncovered source cell."""
    matches = match_text_row(values, columns, file_table, column_tables)
    if any(match is None for match in matches):
        raise MappingDeclarationError("unmapped text replacement") from None
    return tuple(match.replacement for match in matches if match is not None)


def trace_text_row(
    row_ordinal: int, values: tuple[str, ...], columns: tuple[str, ...],
    file_table: TextReplacementTable | None,
    column_tables: Mapping[str, TextReplacementTable],
) -> tuple[TextTraceEvent, ...]:
    """Report only ordinals and match outcomes from the shared row matcher."""
    if type(row_ordinal) is not int or row_ordinal < 1:
        raise MappingDeclarationError("invalid text trace event") from None
    matches = match_text_row(values, columns, file_table, column_tables)
    return tuple(text_trace_event(row_ordinal, ordinal, match)
                 for ordinal, match in enumerate(matches, start=1))


def compile_text_replacement_table(
    payload: bytes, declaration: CsvMapping, *, budget: GenerationBudget,
) -> TextReplacementTable:
    """Compile one-column CSV pairs without type inference or cascading."""
    try:
        if len(declaration.source_columns) != 1 or len(declaration.replacement_columns) != 1:
            raise ValueError
        mapping = parse_csv_mapping_bytes(payload, declaration, budget=budget)
        by_source: dict[str, tuple[str, int]] = {}
        for ordinal, entry in enumerate(mapping.entries, start=1):
            original, replacement = entry.original[0], entry.replacement[0]
            if type(original) is not str or type(replacement) is not str or original == replacement:
                raise ValueError
            by_source[original] = (replacement, ordinal)
        return TextReplacementTable(MappingProxyType(by_source))
    except (ValueError, TypeError, AttributeError):
        pass
    try:
        raise MappingDeclarationError("invalid text replacement table")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise


def parse_csv_mapping_bytes(
    payload: bytes, declaration: CsvMapping, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
    max_rows: int = DEFAULT_MAX_INPUT_ROWS, max_cells: int = DEFAULT_MAX_INPUT_CELLS,
    max_cell_chars: int = DEFAULT_MAX_INPUT_CELL_CHARS, max_columns: int = DEFAULT_MAX_INPUT_COLUMNS,
) -> InlineMapping:
    """Parse bounded CSV pairs."""
    try:
        budget.check("CSV mapping")
        parsed = parse_mapping_declaration(declaration)
        if not isinstance(parsed, CsvMapping):
            raise ValueError
        limits = (max_bytes, max_rows, max_cells, max_cell_chars, max_columns)
        if any(type(limit) is not int or limit < 1 for limit in limits):
            raise ValueError
        if type(payload) is not bytes or len(payload) > max_bytes:
            raise ValueError
        sources, targets = parsed.source_columns, parsed.replacement_columns
        if len(sources) != len(targets) or len(set(sources)) != len(sources) or len(set(targets)) != len(targets):
            raise ValueError
        reader = csv.reader(io.StringIO(payload.decode(parsed.encoding), newline=""),
                            delimiter=parsed.delimiter, strict=True)
        header = next(reader, [])
        budget.check("CSV mapping")
        if len(header) > max_columns:
            raise ValueError
        if not header or any(not name for name in header) or len(header) != len(set(header)):
            raise ValueError
        if set(header) != set(sources) | set(targets):
            raise ValueError
        if any(len(name) > max_cell_chars for name in header):
            raise ValueError
        source_indices = [header.index(name) for name in sources]
        target_indices = [header.index(name) for name in targets]
        entries: list[dict[str, list[str | None]]] = []
        for row in reader:
            budget.check("CSV mapping")
            if len(row) != len(header) or len(entries) >= max_rows:
                raise ValueError
            if (len(entries) + 1) * len(header) > max_cells:
                raise ValueError
            if any(len(value) > max_cell_chars for value in row):
                raise ValueError
            values = [None if parsed.null_token is not None and value == parsed.null_token else value for value in row]
            entries.append({"original": [values[index] for index in source_indices],
                            "replacement": [values[index] for index in target_indices]})
        result = validate_inline_mapping_shape({"kind": "inline", "entries": entries}, key_width=len(sources))
        budget.check("CSV mapping")
        return result
    except (ValueError, csv.Error, UnicodeError):
        pass
    try:
        raise MappingDeclarationError("invalid CSV mapping")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise


_CSV_FLOAT = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def normalize_csv_scalar(value: str, kind: FieldType) -> str | int | float:
    """Use identical numeric keys for CSV mappings and source cells."""
    if kind == FieldType.INTEGER:
        if not re.fullmatch(r"[+-]?[0-9]+", value):
            raise ValueError("invalid CSV number")
        return int(value)
    if kind == FieldType.FLOAT:
        if not _CSV_FLOAT.fullmatch(value):
            raise ValueError("invalid CSV number")
        number = float(value)
        if not math.isfinite(number) or (number == 0.0 and Decimal(value) != 0):
            raise ValueError("invalid CSV number")
        return number
    return value


def normalize_csv_mapping(
    mapping: InlineMapping, *, data_types: tuple[FieldType, ...],
    nullable: tuple[bool, ...], budget: GenerationBudget,
) -> InlineMapping:
    """Normalize declared CSV numbers."""
    try:
        mapping = validate_inline_mapping_shape(mapping, key_width=len(data_types))
        entries: list[dict[str, list[object]]] = []
        for entry in mapping.entries:
            budget.check("CSV mapping normalization")
            converted: dict[str, list[object]] = {}
            for side, values in (("original", entry.original), ("replacement", entry.replacement)):
                converted[side] = []
                for value, kind in zip(values, data_types, strict=True):
                    if value is not None and type(value) is not str:
                        raise ValueError
                    converted[side].append(None if value is None else normalize_csv_scalar(value, kind))
            entries.append(converted)
        result = validate_inline_scalar_mapping(
            {"kind": "inline", "entries": entries}, data_types=data_types, nullable=nullable,
        )
        budget.check("CSV mapping normalization")
        return result
    except ValueError:
        pass
    try:
        raise MappingDeclarationError("invalid typed CSV mapping")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise
