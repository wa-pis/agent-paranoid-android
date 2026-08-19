"""PostgreSQL and Trino adapters for aggregate-only query sources."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.postgres_client import PostgresClient
from test_data_agent.postgres_config import (
    PostgresConfig,
    parse_postgres_column_selector,
    with_resolved_postgres_columns,
)
from test_data_agent.postgres_query_builders import (
    PostgresQuery,
    build_column_discovery_query,
    build_columns_query,
)
from test_data_agent.sql_query_profiling import (
    QueryResultColumn,
    SqlQueryProfileError,
    TrustedProfileQuery,
    profile_validated_query,
)
from test_data_agent.sql_query_source import (
    QuerySourceColumn,
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    SqlQuerySourceError,
    authorize_query_source,
    inspect_query_source,
)
from test_data_agent.trino_client import TrinoClient
from test_data_agent.trino_config import (
    TrinoConfig,
    parse_trino_column_selector,
)
from test_data_agent.trino_query_builders import build_describe_table_query
from test_data_agent.trino_work_budget import (
    consume_profiled_column_work,
    current_query_work_budget,
    query_work_limits_from_env,
    with_query_work_budget,
)


def profile_postgres_query_source(
    request: SqlQueryProfileRequest,
    *,
    config: PostgresConfig,
    driver: Any,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> DatasetProfile:
    if request.adapter is not SqlQueryAdapter.POSTGRES:
        raise SqlQuerySourceError("SQL query adapter does not match PostgreSQL")
    draft = inspect_query_source(request)
    if draft.table_name not in config.allowed_tables:
        raise SqlQuerySourceError("SQL query references an unauthorized table")
    client = PostgresClient(config=config, driver=driver)
    try:
        with client.session() as session:
            columns = _postgres_source_columns(
                config,
                draft.table_parts,
                session.fetch_aggregate_dicts,
            )
            plan = authorize_query_source(draft, columns)
            return profile_validated_query(
                plan,
                describe_query=lambda query: tuple(
                    QueryResultColumn(item.name, item.data_type, item.nullable)
                    for item in session.describe_no_rows(
                        PostgresQuery(query.sql)
                    )
                ),
                fetch_query=lambda query: session.fetch_aggregate_dicts(
                    PostgresQuery(query.sql)
                ),
                local_category_fields=local_category_fields,
            )
    except (SqlQuerySourceError, SqlQueryProfileError):
        raise
    except Exception:
        raise SqlQueryProfileError("SQL query source profiling failed") from None


def profile_trino_query_source(
    request: SqlQueryProfileRequest,
    *,
    config: TrinoConfig,
    driver: Any,
    local_category_fields: Sequence[LocalCategoryField] = (),
) -> DatasetProfile:
    if request.adapter is not SqlQueryAdapter.TRINO:
        raise SqlQuerySourceError("SQL query adapter does not match Trino")
    draft = inspect_query_source(request)
    config.validate_security()
    selectors = _trino_table_selectors(config, draft.table_name)
    client = TrinoClient(config=config, driver=driver)

    def run() -> DatasetProfile:
        catalog, schema, table = draft.table_parts
        metadata_query = build_describe_table_query(catalog, schema, table)
        rows = client.fetch_dicts(metadata_query.sql, metadata_query.parameters)
        columns = _trino_source_columns(rows, selectors)
        plan = authorize_query_source(draft, columns)
        budget = current_query_work_budget()
        if budget is not None:
            budget.consume_projected_columns(len(plan.output_fields))
        consume_profiled_column_work(len(plan.output_fields))

        def describe(query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
            result_rows, description = client.execute_query(query.sql)
            if result_rows:
                raise SqlQueryProfileError(
                    "Trino schema inspection returned an unexpected row"
                )
            return tuple(_trino_description_column(item) for item in description)

        return profile_validated_query(
            plan,
            describe_query=describe,
            fetch_query=lambda query: client.fetch_dicts(query.sql),
            local_category_fields=local_category_fields,
        )

    limits = query_work_limits_from_env(deployment_profile=config.deployment_profile)
    try:
        return with_query_work_budget(run, limits)()
    except (SqlQuerySourceError, SqlQueryProfileError):
        raise
    except Exception:
        raise SqlQueryProfileError("SQL query source profiling failed") from None


def _postgres_source_columns(
    config: PostgresConfig,
    table_parts: tuple[str, ...],
    fetch_query: Any,
) -> tuple[QuerySourceColumn, ...]:
    schema, table = table_parts
    table_name = f"{schema}.{table}"
    selectors = tuple(
        parse_postgres_column_selector(value)
        for value in sorted(config.allowed_columns)
        if value.startswith(f"{table_name}.")
    )
    if not selectors:
        raise SqlQuerySourceError("SQL query table has no allowed columns")
    exact = {
        selector.qualified_name for selector in selectors if not selector.is_wildcard
    }
    if any(selector.is_wildcard for selector in selectors):
        rows = fetch_query(build_column_discovery_query(config, schema, table))
        names = _unique_metadata_names(rows)
        exact.update(f"{table_name}.{name}" for name in names)
    resolved = with_resolved_postgres_columns(config, frozenset(exact))
    rows = fetch_query(build_columns_query(resolved, schema, table))
    expected = {value.rsplit(".", maxsplit=1)[1] for value in exact}
    if {row.get("column_name") for row in rows} != expected or len(rows) != len(expected):
        raise SqlQuerySourceError("SQL query source metadata is incomplete")
    columns = tuple(
        QuerySourceColumn(
            name=_metadata_text(row, "column_name"),
            data_type=_metadata_text(row, "data_type"),
            nullable=_metadata_bool(row, "is_nullable"),
        )
        for row in rows
    )
    return columns


def _trino_table_selectors(
    config: TrinoConfig,
    table_name: str,
) -> tuple[Any, ...]:
    if config.allow_unrestricted or config.allowed_table_columns is None:
        raise SqlQuerySourceError(
            "SQL query profiling requires exact Trino table-column allowlists"
        )
    selectors = tuple(
        parse_trino_column_selector(value)
        for value in sorted(config.allowed_table_columns)
        if value.startswith(f"{table_name}.")
    )
    if not selectors:
        raise SqlQuerySourceError("SQL query references an unauthorized table")
    return selectors


def _trino_source_columns(
    rows: list[dict[str, Any]],
    selectors: tuple[Any, ...],
) -> tuple[QuerySourceColumn, ...]:
    metadata: dict[str, QuerySourceColumn] = {}
    for row in rows:
        name = _metadata_text(row, "column_name")
        if name in metadata:
            raise SqlQuerySourceError("SQL query source metadata is invalid")
        nullable = _metadata_text(row, "is_nullable").upper()
        if nullable not in {"YES", "NO"}:
            raise SqlQuerySourceError("SQL query source metadata is invalid")
        metadata[name] = QuerySourceColumn(
            name=name,
            data_type=_metadata_text(row, "data_type"),
            nullable=nullable == "YES",
        )
    selected = {
        selector.column for selector in selectors if selector.column is not None
    }
    if any(selector.is_wildcard for selector in selectors):
        selected.update(metadata)
    if not selected or not selected.issubset(metadata):
        raise SqlQuerySourceError("SQL query source metadata is incomplete")
    return tuple(metadata[name] for name in sorted(selected))


def _trino_description_column(item: Any) -> QueryResultColumn:
    try:
        name = item[0]
        type_code = item[1]
        nullable = item[6] if len(item) > 6 else None
    except (IndexError, TypeError):
        raise SqlQueryProfileError("Trino schema metadata is invalid") from None
    type_name = getattr(type_code, "name", None) or str(type_code)
    if not isinstance(name, str) or not name or not type_name:
        raise SqlQueryProfileError("Trino schema metadata is invalid")
    return QueryResultColumn(name=name, data_type=type_name, nullable=nullable is not False)


def _unique_metadata_names(rows: list[dict[str, object]]) -> tuple[str, ...]:
    names = tuple(_metadata_text(row, "column_name") for row in rows)
    if not names or len(names) != len(set(names)):
        raise SqlQuerySourceError("SQL query source metadata is invalid")
    return names


def _metadata_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise SqlQuerySourceError("SQL query source metadata is invalid")
    return value


def _metadata_bool(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    if type(value) is not bool:
        raise SqlQuerySourceError("SQL query source metadata is invalid")
    return value


__all__ = ["profile_postgres_query_source", "profile_trino_query_source"]
