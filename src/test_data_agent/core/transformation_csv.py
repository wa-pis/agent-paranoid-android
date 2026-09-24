"""Private bounded CSV mapping parsing; no filesystem access or type inference."""

import csv
import io
import math
import re
from decimal import Decimal

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


def parse_csv_mapping_bytes(
    payload: bytes, declaration: CsvMapping, *, encoding: str, delimiter: str,
    null_token: str | None, budget: GenerationBudget, max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
    max_rows: int = DEFAULT_MAX_INPUT_ROWS, max_cells: int = DEFAULT_MAX_INPUT_CELLS,
    max_cell_chars: int = DEFAULT_MAX_INPUT_CELL_CHARS, max_columns: int = DEFAULT_MAX_INPUT_COLUMNS,
) -> InlineMapping:
    """Return private string/null pairs; caller must perform typed preflight."""
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
        if encoding not in ("utf-8", "utf-8-sig") or delimiter not in (",", ";", "\t", "|"):
            raise ValueError
        if null_token is not None and (type(null_token) is not str or not null_token):
            raise ValueError
        sources, targets = parsed.source_columns, parsed.replacement_columns
        if len(sources) != len(targets) or len(set(sources)) != len(sources) or len(set(targets)) != len(targets):
            raise ValueError
        reader = csv.reader(io.StringIO(payload.decode(encoding), newline=""), delimiter=delimiter, strict=True)
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
            values = [None if value == null_token else value for value in row]
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


_CSV_FLOAT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def normalize_csv_mapping(
    mapping: InlineMapping, *, data_types: tuple[FieldType, ...],
    nullable: tuple[bool, ...], budget: GenerationBudget,
) -> InlineMapping:
    """Normalize declared CSV integers/floats; reject ambiguous numeric text."""
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
                    if value is not None and kind == FieldType.INTEGER:
                        if not isinstance(value, str) or not re.fullmatch(r"[+-]?[0-9]+", value):
                            raise ValueError
                        converted[side].append(int(value))
                    elif value is not None and kind == FieldType.FLOAT:
                        if not _CSV_FLOAT.fullmatch(value):
                            raise ValueError
                        number = float(value)
                        if not math.isfinite(number) or (number == 0.0 and Decimal(value) != 0):
                            raise ValueError
                        converted[side].append(number)
                    else:
                        converted[side].append(value)
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
