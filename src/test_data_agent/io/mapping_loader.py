"""Private CSV mapping loading from one bounded local byte snapshot."""

from dataclasses import dataclass, field
from pathlib import Path

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_csv import parse_csv_mapping_bytes
from test_data_agent.core.transformation_mapping import (
    CsvMapping, InlineMapping, MappingDeclarationError, parse_mapping_declaration,
    validate_inline_scalar_mapping,
)
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot


@dataclass(frozen=True)
class LoadedCsvMapping:
    mapping: InlineMapping = field(repr=False)
    source_sha256: str = field(repr=False)


def load_csv_mapping(
    root: Path, declaration: CsvMapping, *, data_types: tuple[FieldType, ...],
    nullable: tuple[bool, ...], encoding: str, delimiter: str, null_token: str | None,
    max_bytes: int, max_rows: int, max_cells: int, max_columns: int,
    max_cell_chars: int, budget: GenerationBudget,
) -> LoadedCsvMapping:
    """Load private string/date mappings; no numeric coercion or approval."""
    parsed = parse_mapping_declaration(declaration)
    if not isinstance(parsed, CsvMapping):
        try:
            raise MappingDeclarationError("invalid CSV mapping declaration")
        except MappingDeclarationError as error:
            error.__context__ = None
            raise
    snapshot = read_mapping_snapshot(root, parsed.path, max_bytes=max_bytes, budget=budget)
    mapping = parse_csv_mapping_bytes(
        snapshot.payload, parsed, encoding=encoding, delimiter=delimiter,
        null_token=null_token, budget=budget, max_bytes=max_bytes, max_rows=max_rows,
        max_cells=max_cells, max_columns=max_columns, max_cell_chars=max_cell_chars,
    )
    validated = validate_inline_scalar_mapping(mapping, data_types=data_types, nullable=nullable)
    # Reuse the invocation deadline even after the final typed validation pass.
    try:
        budget.check("CSV mapping")
    except ValueError:
        try:
            raise MappingDeclarationError("invalid CSV mapping")
        except MappingDeclarationError as error:
            error.__context__ = None
            raise
    return LoadedCsvMapping(validated, snapshot.sha256)
