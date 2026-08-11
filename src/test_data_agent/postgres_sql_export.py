"""Deterministic PostgreSQL DDL and INSERT export for generated datasets."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.limits import enforce_output_payload_size
from test_data_agent.csv_profiler import (
    parse_bool,
    parse_date_value,
    parse_datetime_value,
    parse_float,
    parse_int,
)
from test_data_agent.io.path_policy import atomic_write_bytes
from test_data_agent.validation.reconciliation import validate_dataset


class PostgresSqlExportError(ValueError):
    """Raised when generated data cannot be represented as PostgreSQL SQL."""


def render_postgres_sql(
    spec: DatasetSpec,
    rows_by_entity: Mapping[str, Sequence[Mapping[str, Any]]],
) -> str:
    """Render one transaction containing deterministic PostgreSQL DDL and rows."""

    normalized_rows = {
        entity: [dict(row) for row in rows]
        for entity, rows in rows_by_entity.items()
    }
    if not validate_dataset(normalized_rows, spec).valid:
        raise PostgresSqlExportError("PostgreSQL SQL export requires a valid dataset")
    entities = {entity.name: entity for entity in spec.entities}
    order = _dependency_order(spec)
    statements = ["BEGIN;", "SET LOCAL standard_conforming_strings = on;"]
    statements.extend(_create_table(entities[name]) for name in order)
    statements.extend(_foreign_key_statements(spec))
    for name in order:
        statements.extend(_insert_statements(entities[name], normalized_rows[name]))
    statements.append("COMMIT;")
    return "\n\n".join(statements) + "\n"


def write_postgres_sql(
    spec: DatasetSpec,
    rows_by_entity: Mapping[str, Sequence[Mapping[str, Any]]],
    output: Path,
) -> None:
    """Atomically publish a complete PostgreSQL SQL file."""

    if output.suffix.lower() != ".sql":
        raise PostgresSqlExportError("PostgreSQL SQL output must use a .sql suffix")
    payload = render_postgres_sql(spec, rows_by_entity).encode("utf-8")
    enforce_output_payload_size(len(payload), label="PostgreSQL SQL output")
    atomic_write_bytes(output, payload)


def quote_postgres_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise PostgresSqlExportError("PostgreSQL identifier is invalid")
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def postgres_literal(value: Any, field_type: FieldType) -> str:
    if value is None:
        return "NULL"
    if field_type == FieldType.INTEGER:
        parsed = (
            value
            if type(value) is int
            else parse_int(value)
            if isinstance(value, str)
            else None
        )
        if parsed is None:
            raise PostgresSqlExportError("PostgreSQL integer value is invalid")
        return str(parsed)
    if field_type == FieldType.FLOAT:
        parsed_float = (
            float(value)
            if type(value) in {int, float}
            else parse_float(value)
            if isinstance(value, str)
            else None
        )
        if parsed_float is None or not math.isfinite(parsed_float):
            raise PostgresSqlExportError("PostgreSQL float value is invalid")
        return repr(parsed_float)
    if field_type == FieldType.BOOLEAN:
        parsed_bool = (
            value
            if type(value) is bool
            else parse_bool(value)
            if isinstance(value, str)
            else None
        )
        if parsed_bool is None:
            raise PostgresSqlExportError("PostgreSQL boolean value is invalid")
        return "TRUE" if parsed_bool else "FALSE"
    if field_type == FieldType.DATE:
        parsed_date = (
            value
            if type(value) is date
            else parse_date_value(value)
            if isinstance(value, str)
            else None
        )
        if parsed_date is None:
            raise PostgresSqlExportError("PostgreSQL date value is invalid")
        return f"DATE '{parsed_date.isoformat()}'"
    if field_type == FieldType.DATETIME:
        parsed_datetime = (
            value
            if isinstance(value, datetime)
            else parse_datetime_value(value)
            if isinstance(value, str)
            else None
        )
        if parsed_datetime is None:
            raise PostgresSqlExportError("PostgreSQL datetime value is invalid")
        text = parsed_datetime.isoformat(sep=" ")
        return f"TIMESTAMPTZ '{text}'"
    if field_type == FieldType.STRING and isinstance(value, str):
        if "\x00" in value:
            raise PostgresSqlExportError("PostgreSQL string value is unsupported")
        return f"'{value.replace(chr(39), chr(39) * 2)}'"
    raise PostgresSqlExportError("PostgreSQL scalar value is unsupported")


def _create_table(entity: EntitySpec) -> str:
    if not entity.fields:
        raise PostgresSqlExportError("PostgreSQL tables require at least one field")
    definitions = [
        f"  {quote_postgres_identifier(field.name)} {_postgres_type(field)}"
        f"{' NOT NULL' if not field.nullable or field.name == entity.primary_key else ''}"
        for field in entity.fields
    ]
    if entity.primary_key is not None:
        definitions.append(
            f"  PRIMARY KEY ({quote_postgres_identifier(entity.primary_key)})"
        )
    body = ",\n".join(definitions)
    return f"CREATE TABLE {quote_postgres_identifier(entity.name)} (\n{body}\n);"


def _postgres_type(field: FieldSpec) -> str:
    return {
        FieldType.INTEGER: "BIGINT",
        FieldType.FLOAT: "DOUBLE PRECISION",
        FieldType.BOOLEAN: "BOOLEAN",
        FieldType.STRING: "TEXT",
        FieldType.DATE: "DATE",
        FieldType.DATETIME: "TIMESTAMP WITH TIME ZONE",
    }[field.data_type]


def _foreign_key_statements(spec: DatasetSpec) -> list[str]:
    entities = {entity.name: entity for entity in spec.entities}
    statements: list[str] = []
    for index, relationship in enumerate(
        sorted(
            spec.relationships,
            key=lambda item: (
                item.child_entity,
                item.child_field,
                item.parent_entity,
                item.parent_field,
            ),
        ),
        start=1,
    ):
        parent = entities[relationship.parent_entity]
        child = entities[relationship.child_entity]
        if parent.primary_key != relationship.parent_field:
            raise PostgresSqlExportError(
                "PostgreSQL foreign keys must reference a declared primary key"
            )
        if (
            parent.field(relationship.parent_field).data_type
            != child.field(relationship.child_field).data_type
        ):
            raise PostgresSqlExportError(
                "PostgreSQL foreign-key field types must match"
            )
        constraint = quote_postgres_identifier(f"fk_{index:04d}")
        statements.append(
            f"ALTER TABLE {quote_postgres_identifier(relationship.child_entity)} "
            f"ADD CONSTRAINT {constraint} "
            f"FOREIGN KEY ({quote_postgres_identifier(relationship.child_field)}) "
            f"REFERENCES {quote_postgres_identifier(relationship.parent_entity)} "
            f"({quote_postgres_identifier(relationship.parent_field)}) "
            "DEFERRABLE INITIALLY DEFERRED;"
        )
    return statements


def _insert_statements(
    entity: EntitySpec,
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    columns = ", ".join(
        quote_postgres_identifier(field.name) for field in entity.fields
    )
    statements: list[str] = []
    for row in rows:
        values = ", ".join(
            postgres_literal(row[field.name], field.data_type) for field in entity.fields
        )
        statements.append(
            f"INSERT INTO {quote_postgres_identifier(entity.name)} "
            f"({columns}) VALUES ({values});"
        )
    return statements


def _dependency_order(spec: DatasetSpec) -> list[str]:
    names = {entity.name for entity in spec.entities}
    parents: dict[str, set[str]] = {name: set() for name in names}
    for relationship in spec.relationships:
        parents[relationship.child_entity].add(relationship.parent_entity)
    order: list[str] = []
    remaining = set(names)
    while remaining:
        ready = sorted(name for name in remaining if not (parents[name] & remaining))
        if not ready:
            order.extend(sorted(remaining))
            break
        order.extend(ready)
        remaining.difference_update(ready)
    return order


__all__ = [
    "PostgresSqlExportError",
    "postgres_literal",
    "quote_postgres_identifier",
    "render_postgres_sql",
    "write_postgres_sql",
]
