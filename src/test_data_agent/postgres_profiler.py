"""Normalize bounded PostgreSQL metadata and aggregates into DatasetProfile."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.privacy import (
    LocalCategoryField,
    validate_local_category_values,
)
from test_data_agent.core.relationship import Relationship
from test_data_agent.postgres_client import PostgresClient
from test_data_agent.postgres_config import (
    PostgresConfig,
    PostgresConfigurationError,
    parse_postgres_column_selector,
    with_resolved_postgres_columns,
)
from test_data_agent.postgres_query_builders import (
    PostgresQuery,
    build_column_summary_query,
    build_column_discovery_query,
    build_columns_query,
    build_foreign_keys_query,
    build_list_tables_query,
    build_local_category_candidates_query,
    build_numeric_shape_query,
    build_primary_keys_query,
    build_table_row_count_query,
)
from test_data_agent.profile_types import ProfileDataType, coerce_profile_type


class PostgresProfileError(RuntimeError):
    """Raised when bounded PostgreSQL results cannot form a complete profile."""


QueryFetcher = Callable[[PostgresQuery], list[dict[str, object]]]


@dataclass(frozen=True)
class PostgresProfiler:
    config: PostgresConfig
    fetch_query: QueryFetcher

    def profile(
        self,
        *,
        local_category_fields: Sequence[LocalCategoryField] = (),
    ) -> DatasetProfile:
        self.config.validate()
        categories = tuple(local_category_fields)
        table_rows = self.fetch_query(build_list_tables_query(self.config))
        tables = self._complete_tables(table_rows)
        profiler = replace(self, config=self._expanded_config(tables))
        entities = [profiler._profile_table(*table, categories) for table in tables]
        relationships = profiler._relationships(entities)
        return DatasetProfile(
            source_type="postgres",
            entities=entities,
            relationships=relationships,
            local_category_fields=list(categories),
        )

    def _expanded_config(
        self,
        tables: Sequence[tuple[str, str]],
    ) -> PostgresConfig:
        selectors = tuple(
            parse_postgres_column_selector(value)
            for value in sorted(self.config.allowed_columns)
        )
        explicit = {
            selector.qualified_name
            for selector in selectors
            if not selector.is_wildcard
        }
        for selector in selectors:
            if not selector.is_wildcard:
                continue
            rows = self.fetch_query(
                build_column_discovery_query(
                    self.config,
                    selector.schema,
                    selector.table,
                )
            )
            discovered = self._discovered_column_names(
                selector.schema,
                selector.table,
                rows,
            )
            explicit.update(
                f"{selector.schema}.{selector.table}.{column}"
                for column in discovered
            )
        table_names = {f"{schema}.{table}" for schema, table in tables}
        covered_tables = {
            ".".join(column.split(".", maxsplit=2)[:2]) for column in explicit
        }
        if covered_tables != table_names:
            raise PostgresProfileError(
                "PostgreSQL column selectors do not cover every allowed table"
            )
        if len(explicit) > self.config.limits.max_columns:
            raise PostgresProfileError(
                "PostgreSQL expanded column snapshot exceeds its budget"
            )
        return with_resolved_postgres_columns(
            self.config,
            frozenset(explicit),
        )

    def _discovered_column_names(
        self,
        schema: str,
        table: str,
        rows: Sequence[dict[str, object]],
    ) -> tuple[str, ...]:
        names = [_required_text(row, "column_name") for row in rows]
        if not names or len(names) != len(set(names)):
            raise PostgresProfileError(
                "PostgreSQL wildcard column metadata is incomplete"
            )
        try:
            selectors = tuple(
                parse_postgres_column_selector(f"{schema}.{table}.{name}")
                for name in names
            )
        except PostgresConfigurationError:
            raise PostgresProfileError(
                "PostgreSQL wildcard column metadata is invalid"
            ) from None
        if len(selectors) > self.config.limits.max_columns:
            raise PostgresProfileError(
                "PostgreSQL expanded column snapshot exceeds its budget"
            )
        return tuple(sorted(selector.column for selector in selectors if selector.column))

    def _complete_tables(
        self, rows: Sequence[dict[str, object]]
    ) -> tuple[tuple[str, str], ...]:
        discovered = {
            (_required_text(row, "table_schema"), _required_text(row, "table_name"))
            for row in rows
        }
        expected = {
            tuple(table.split(".", maxsplit=1)) for table in self.config.allowed_tables
        }
        if discovered != expected or len(rows) != len(discovered):
            raise PostgresProfileError(
                "PostgreSQL table metadata does not match the configured allowlist"
            )
        return tuple(sorted(discovered))

    def _profile_table(
        self,
        schema: str,
        table: str,
        local_category_fields: Sequence[LocalCategoryField],
    ) -> EntityProfile:
        entity_name = f"{self.config.source_id}.{schema}.{table}"
        column_rows = self.fetch_query(build_columns_query(self.config, schema, table))
        columns = self._complete_columns(schema, table, column_rows)
        row_count = _non_negative_int(
            _single_row(
                self.fetch_query(
                    build_table_row_count_query(self.config, schema, table)
                ),
                "table row count",
            ).get("row_count"),
            "table row count",
        )
        category_fields = {
            field.field: field
            for field in local_category_fields
            if field.entity == entity_name
        }
        profile_columns = [
            self._profile_column(
                schema,
                table,
                row_count,
                column,
                category_fields.get(_required_text(column, "column_name")),
            )
            for column in columns
        ]
        profile = legacy_profile_to_dataset_profile(
            {
                "table": entity_name,
                "row_count": row_count,
                "columns": profile_columns,
                "local_category_fields": list(category_fields.values()),
            },
            source_type="postgres",
        ).entities[0]
        primary_key_rows = self.fetch_query(
            build_primary_keys_query(self.config, schema, table)
        )
        primary_keys = [_required_text(row, "column_name") for row in primary_key_rows]
        if len(primary_keys) != len(set(primary_keys)) or any(
            key not in {field.name for field in profile.fields} for key in primary_keys
        ):
            raise PostgresProfileError("PostgreSQL primary-key metadata is invalid")
        return profile.model_copy(update={"primary_key_candidates": primary_keys})

    def _complete_columns(
        self,
        schema: str,
        table: str,
        rows: Sequence[dict[str, object]],
    ) -> tuple[dict[str, object], ...]:
        expected = {
            value.split(".", maxsplit=2)[2]
            for value in (self.config.resolved_columns or self.config.allowed_columns)
            if value.startswith(f"{schema}.{table}.")
        }
        discovered = [_required_text(row, "column_name") for row in rows]
        if set(discovered) != expected or len(discovered) != len(set(discovered)):
            raise PostgresProfileError(
                "PostgreSQL column metadata does not match the configured allowlist"
            )
        return tuple(
            sorted(rows, key=lambda row: _non_negative_int(row.get("ordinal_position"), "column order"))
        )

    def _profile_column(
        self,
        schema: str,
        table: str,
        row_count: int,
        column: dict[str, object],
        local_category_field: LocalCategoryField | None,
    ) -> dict[str, object]:
        name = _required_text(column, "column_name")
        data_type = _required_text(column, "data_type")
        summary = _single_row(
            self.fetch_query(
                build_column_summary_query(self.config, schema, table, name)
            ),
            "column summary",
        )
        summary_row_count = _non_negative_int(summary.get("row_count"), "column row count")
        non_null_count = _non_negative_int(
            summary.get("non_null_count"), "column non-null count"
        )
        distinct_count = _non_negative_int(
            summary.get("distinct_count"), "column distinct count"
        )
        if (
            summary_row_count != row_count
            or non_null_count > row_count
            or distinct_count > non_null_count
        ):
            raise PostgresProfileError("PostgreSQL column aggregate counts are invalid")
        result: dict[str, object] = {
            "name": name,
            "data_type": data_type,
            "nullable": _as_bool(column.get("is_nullable")),
            "null_ratio": (row_count - non_null_count) / row_count if row_count else 0.0,
            "approx_distinct_count": distinct_count,
        }
        if coerce_profile_type(data_type) in {
            ProfileDataType.INTEGER,
            ProfileDataType.FLOAT,
        }:
            shape = _single_row(
                self.fetch_query(
                    build_numeric_shape_query(self.config, schema, table, name)
                ),
                "numeric shape",
            )
            has_negative = _as_bool(shape.get("has_negative"))
            has_positive = _as_bool(shape.get("has_positive"))
            magnitude = shape.get("max_abs_magnitude")
            if magnitude is not None and (has_negative or has_positive):
                result["numeric_shape"] = {
                    "max_abs_magnitude": _bounded_magnitude(magnitude),
                    "has_negative": has_negative,
                    "has_positive": has_positive,
                }
        if local_category_field is not None:
            category_rows = self.fetch_query(
                build_local_category_candidates_query(
                    self.config, local_category_field
                )
            )
            values = [row.get("value") for row in category_rows]
            validate_local_category_values(
                field_name=name,
                semantic_type=None,
                sensitive=False,
                values=values,
            )
            counts = [
                _positive_int(row.get("count"), "category count")
                for row in category_rows
            ]
            top_values = [
                {
                    "value": row.get("value"),
                    "count": count,
                }
                for row, count in zip(category_rows, counts, strict=True)
            ]
            if (
                len(top_values) != distinct_count
                or sum(counts) != non_null_count
            ):
                raise PostgresProfileError(
                    "PostgreSQL local category aggregate is incomplete"
                )
            result["top_values"] = top_values
        return result

    def _relationships(self, entities: Sequence[EntityProfile]) -> list[Relationship]:
        fields = {entity.name: {field.name for field in entity.fields} for entity in entities}
        relationships: list[Relationship] = []
        seen: set[tuple[str, str, str, str]] = set()
        for row in self.fetch_query(build_foreign_keys_query(self.config)):
            child = self._entity_name(row, "table_schema", "table_name")
            parent = self._entity_name(
                row, "referenced_table_schema", "referenced_table_name"
            )
            child_field = _required_text(row, "column_name")
            parent_field = _required_text(row, "referenced_column_name")
            key = (parent, parent_field, child, child_field)
            if (
                key in seen
                or parent_field not in fields.get(parent, set())
                or child_field not in fields.get(child, set())
            ):
                raise PostgresProfileError("PostgreSQL foreign-key metadata is invalid")
            seen.add(key)
            relationships.append(
                Relationship(
                    parent_entity=parent,
                    parent_field=parent_field,
                    child_entity=child,
                    child_field=child_field,
                    confidence=1.0,
                    status="declared",
                )
            )
        return relationships

    def _entity_name(
        self, row: dict[str, object], schema_key: str, table_key: str
    ) -> str:
        return (
            f"{self.config.source_id}."
            f"{_required_text(row, schema_key)}.{_required_text(row, table_key)}"
        )


def dataset_profile_from_postgres(
    client: PostgresClient,
    *,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> DatasetProfile:
    """Profile one PostgreSQL source through its bounded read-only session."""

    with client.session() as session:
        return PostgresProfiler(
            config=client.config,
            fetch_query=session.fetch_aggregate_dicts,
        ).profile(local_category_fields=local_category_fields)


def _single_row(
    rows: Sequence[dict[str, object]], label: str
) -> dict[str, object]:
    if len(rows) != 1:
        raise PostgresProfileError(f"PostgreSQL {label} result is incomplete")
    return rows[0]


def _required_text(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise PostgresProfileError("PostgreSQL metadata contains an invalid text field")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise PostgresProfileError(f"PostgreSQL {label} is invalid")
    return value


def _positive_int(value: object, label: str) -> int:
    result = _non_negative_int(value, label)
    if result == 0:
        raise PostgresProfileError(f"PostgreSQL {label} is invalid")
    return result


def _bounded_magnitude(value: object) -> int:
    if type(value) is not int or not -308 <= value <= 307:
        raise PostgresProfileError("PostgreSQL numeric magnitude is invalid")
    return value


def _as_bool(value: object) -> bool:
    if type(value) is bool:
        return value
    if isinstance(value, str) and value.upper() in {"YES", "NO"}:
        return value.upper() == "YES"
    if value is None:
        return False
    raise PostgresProfileError("PostgreSQL metadata contains an invalid boolean")


__all__ = [
    "PostgresProfileError",
    "PostgresProfiler",
    "dataset_profile_from_postgres",
]
