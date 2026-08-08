"""Safe Trino MCP tools for schema inspection and profiling.

The public helpers in this module are intentionally small and conservative so
they can be tested without a live Trino cluster.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
from typing import Any

from test_data_agent.audit import audit_logger_from_env
from test_data_agent.mcp_trino_transport import (
    create_trino_mcp,
    run_bounded_trino_mcp,
)
from test_data_agent.trino_config import (
    ABSOLUTE_MAX_RESULT_ROWS as ABSOLUTE_MAX_RESULT_ROWS,
    DATA_SIZE_MULTIPLIERS as DATA_SIZE_MULTIPLIERS,
    DATA_SIZE_RE as DATA_SIZE_RE,
    DEFAULT_MAX_RESULT_ROWS as DEFAULT_MAX_RESULT_ROWS,
    DEFAULT_QUERY_MAX_EXECUTION_TIME as DEFAULT_QUERY_MAX_EXECUTION_TIME,
    DEFAULT_QUERY_MAX_RUN_TIME as DEFAULT_QUERY_MAX_RUN_TIME,
    DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES as DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES,
    DURATION_MULTIPLIERS_MS as DURATION_MULTIPLIERS_MS,
    DURATION_RE as DURATION_RE,
    MAX_QUERY_EXECUTION_TIME_MS as MAX_QUERY_EXECUTION_TIME_MS,
    MAX_QUERY_RUN_TIME_MS as MAX_QUERY_RUN_TIME_MS,
    MAX_QUERY_SCAN_BYTES as MAX_QUERY_SCAN_BYTES,
    TrinoConfig as TrinoConfig,
    TrinoConfigurationError as TrinoConfigurationError,
    parse_allowlist as parse_allowlist,
    parse_data_size_env as parse_data_size_env,
    parse_data_size_value as parse_data_size_value,
    parse_duration_env as parse_duration_env,
    parse_duration_value as parse_duration_value,
    parse_env_bool as parse_env_bool,
    parse_max_result_rows as parse_max_result_rows,
    parse_request_timeout as parse_request_timeout,
    parse_trino_port as parse_trino_port,
)
from test_data_agent.trino_client import (
    TrinoClient as TrinoClient,
    TrinoResultLimitError as TrinoResultLimitError,
    rows_to_dicts as rows_to_dicts,
    trino as trino,
)
from test_data_agent.trino_masking import (
    TrinoMasker as TrinoMasker,
    infer_sensitive_from_name as infer_sensitive_from_name,
    infer_sensitive_type_from_values as infer_sensitive_type_from_values,
    infer_sensitive_value_type as infer_sensitive_value_type,
    looks_sensitive_value as looks_sensitive_value,
    mask_pattern as mask_pattern,
    mask_row as mask_row,
    mask_value as mask_value,
    summarize_top_values as summarize_top_values,
    synthetic_category_distribution as synthetic_category_distribution,
)
from test_data_agent.trino_profiling import (
    MIN_RULE_CONFIDENCE as MIN_RULE_CONFIDENCE,
    TrinoProfiler as TrinoProfiler,
    first_row as first_row,
    rule_profile as rule_profile,
)
from test_data_agent.trino_query_builders import (
    FormulaSql as FormulaSql,
    TrinoQuery as TrinoQuery,
    bounded_limit as bounded_limit,
    build_aggregate_mapping_profile_query as build_aggregate_mapping_profile_query,
    build_column_cardinality_query as build_column_cardinality_query,
    build_column_profile_query as build_column_profile_query,
    build_conditional_allowed_values_profile_query as build_conditional_allowed_values_profile_query,
    build_conditional_required_profile_query as build_conditional_required_profile_query,
    build_describe_table_query as build_describe_table_query,
    build_foreign_key_profile_query as build_foreign_key_profile_query,
    build_formula_rule_profile_query as build_formula_rule_profile_query,
    build_formula_sql as build_formula_sql,
    build_list_catalogs_query as build_list_catalogs_query,
    build_list_schemas_query as build_list_schemas_query,
    build_list_tables_query as build_list_tables_query,
    build_table_profile_query as build_table_profile_query,
    build_temporal_ordering_profile_query as build_temporal_ordering_profile_query,
    build_top_values_query as build_top_values_query,
    formula_node_to_sql as formula_node_to_sql,
    is_date_trino_type as is_date_trino_type,
    is_numeric_trino_type as is_numeric_trino_type,
    is_string_trino_type as is_string_trino_type,
    is_timestamp_trino_type as is_timestamp_trino_type,
    present_sql as present_sql,
    profile_column_sql as profile_column_sql,
    qualified_table as qualified_table,
    require_non_negative_float as require_non_negative_float,
)
from test_data_agent.trino_sql_policy import (
    FORBIDDEN_SQL_RE as FORBIDDEN_SQL_RE,
    IDENTIFIER_RE as IDENTIFIER_RE,
    LIMIT_RE as LIMIT_RE,
    MAX_LIMIT as MAX_LIMIT,
    SELECT_STAR_RE as SELECT_STAR_RE,
    TABLE_STAR_RE as TABLE_STAR_RE,
    AllowlistError as AllowlistError,
    SqlSafetyError as SqlSafetyError,
    check_allowlist as check_allowlist,
    exp as exp,
    extract_table_references as extract_table_references,
    has_top_level_limit as has_top_level_limit,
    has_unrestricted_projection_star as has_unrestricted_projection_star,
    is_star_column as is_star_column,
    normalize_sql as normalize_sql,
    parse_select_ast as parse_select_ast,
    quote_identifier as quote_identifier,
    require_identifier as require_identifier,
    selected_sensitive_identifier_names as selected_sensitive_identifier_names,
    sqlglot as sqlglot,
    strip_sql_comments as strip_sql_comments,
    top_level_limit_value as top_level_limit_value,
    unquoted_char_positions as unquoted_char_positions,
    validate_safe_select as validate_safe_select,
    validate_safe_select_shape as validate_safe_select_shape,
    validate_table_references_allowed as validate_table_references_allowed,
)
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudget,
    QueryWorkLimits,
    query_work_limits_from_env,
    with_query_work_budget,
)

DEFAULT_LIMIT = 100
ENABLE_SAFE_SELECT_ENV = "TRINO_ENABLE_SAFE_SELECT"


def _execute_query(
    sql: str, parameters: Sequence[Any] | None = None
) -> tuple[list[tuple[Any, ...]], list[Any]]:
    client = TrinoClient(config=TrinoConfig.from_env(), driver=trino)
    return client.execute_query(sql, parameters)


def _fetch_dicts(
    sql: str, parameters: Sequence[Any] | None = None
) -> list[dict[str, Any]]:
    client = TrinoClient(config=TrinoConfig.from_env(), driver=trino)
    return client.fetch_dicts(sql, parameters)


def _fetch_built_query(query: TrinoQuery) -> list[dict[str, Any]]:
    parameters = list(query.parameters) if query.parameters else None
    return _fetch_dicts(query.sql, parameters)


def _trino_profiler() -> TrinoProfiler:
    return TrinoProfiler(
        config=TrinoConfig.from_env(),
        fetch_query=_fetch_built_query,
    )


def _trino_masker() -> TrinoMasker:
    return TrinoMasker(
        config=TrinoConfig.from_env(),
        fetch_query=_fetch_built_query,
        fetch_sql=_fetch_dicts,
    )


def list_catalogs() -> list[str]:
    return _trino_profiler().list_catalogs()


def list_schemas(catalog: str) -> list[str]:
    return _trino_profiler().list_schemas(catalog)


def list_tables(catalog: str, schema: str) -> list[str]:
    return _trino_profiler().list_tables(catalog, schema)


def describe_table(catalog: str, schema: str, table: str) -> list[dict[str, Any]]:
    return _trino_profiler().describe_table(catalog, schema, table)


def profile_table(catalog: str, schema: str, table: str) -> dict[str, Any]:
    return _trino_profiler().profile_table(catalog, schema, table)


def profile_column(
    catalog: str, schema: str, table: str, column: str
) -> dict[str, Any]:
    return _trino_profiler().profile_column(catalog, schema, table, column)


def profile_table_safe(
    catalog: str, schema: str, table: str, max_top_values: int = 20
) -> dict[str, Any]:
    """Build a safe Trino-derived profile using pushdown aggregates only."""
    return _trino_profiler().profile_table_safe(
        catalog,
        schema,
        table,
        max_top_values,
        profile_column_safe,
    )


def profile_column_safe(
    catalog: str,
    schema: str,
    table: str,
    column: str,
    data_type: str,
    nullable: bool,
    max_top_values: int,
) -> dict[str, Any]:
    return _trino_masker().profile_column_safe(
        catalog,
        schema,
        table,
        column,
        data_type,
        nullable,
        max_top_values,
    )


def profile_foreign_key(
    catalog: str,
    schema: str,
    parent_table: str,
    parent_field: str,
    child_table: str,
    child_field: str,
) -> dict[str, Any]:
    """Profile foreign-key coverage using counts only."""
    return _trino_profiler().profile_foreign_key(
        catalog,
        schema,
        parent_table,
        parent_field,
        child_table,
        child_field,
    )


def profile_temporal_ordering(
    catalog: str,
    schema: str,
    table: str,
    start_field: str,
    end_field: str,
    allow_equal: bool = True,
) -> dict[str, Any]:
    """Profile temporal ordering with pass/fail counts only."""
    return _trino_profiler().profile_temporal_ordering(
        catalog,
        schema,
        table,
        start_field,
        end_field,
        allow_equal,
    )


def profile_formula_rule(
    catalog: str,
    schema: str,
    table: str,
    target_field: str,
    expression: str,
    tolerance: float = 0.000001,
) -> dict[str, Any]:
    """Profile a numeric row formula without returning source values."""
    return _trino_profiler().profile_formula_rule(
        catalog,
        schema,
        table,
        target_field,
        expression,
        tolerance,
    )


def profile_conditional_required(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    required_field: str,
) -> dict[str, Any]:
    """Profile conditional requiredness without exposing condition values."""
    return _trino_profiler().profile_conditional_required(
        catalog,
        schema,
        table,
        condition_field,
        condition_equals,
        required_field,
    )


def profile_conditional_allowed_values(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    value_field: str,
    allowed_values: list[Any],
) -> dict[str, Any]:
    """Profile conditional allowed-values consistency with counts only."""
    return _trino_profiler().profile_conditional_allowed_values(
        catalog,
        schema,
        table,
        condition_field,
        condition_equals,
        value_field,
        allowed_values,
    )


def profile_aggregate_mapping(
    catalog: str,
    schema: str,
    parent_table: str,
    parent_key: str,
    parent_value_field: str,
    child_table: str,
    child_key: str,
    child_value_field: str | None = None,
    aggregate: str = "sum",
    tolerance: float = 0.000001,
) -> dict[str, Any]:
    """Profile whether parent aggregate fields match child aggregates."""
    return _trino_profiler().profile_aggregate_mapping(
        catalog,
        schema,
        parent_table,
        parent_key,
        parent_value_field,
        child_table,
        child_key,
        child_value_field,
        aggregate,
        tolerance,
    )


def run_safe_select(sql: str) -> list[dict[str, Any]]:
    return _trino_masker().run_safe_select(sql)


def trino_mcp_tools() -> list[Callable[..., Any]]:
    tools: list[Callable[..., Any]] = [
        list_catalogs,
        list_schemas,
        list_tables,
        describe_table,
        profile_table,
        profile_column,
        profile_table_safe,
        profile_foreign_key,
        profile_temporal_ordering,
        profile_formula_rule,
        profile_conditional_required,
        profile_conditional_allowed_values,
        profile_aggregate_mapping,
    ]
    if parse_env_bool(ENABLE_SAFE_SELECT_ENV):
        tools.append(run_safe_select)
    return tools


def trino_mcp_services(
    *,
    work_limits: QueryWorkLimits = DEFAULT_QUERY_WORK_LIMITS,
    budget_provider: Callable[[], QueryWorkBudget | None] | None = None,
) -> list[Callable[..., Any]]:
    return [
        with_query_work_budget(
            tool,
            work_limits,
            budget_provider=budget_provider,
        )
        for tool in trino_mcp_tools()
    ]


def _new_transport_query_work_budget(
    raw_payload_bytes: int,
    *,
    work_limits: QueryWorkLimits = DEFAULT_QUERY_WORK_LIMITS,
) -> QueryWorkBudget:
    budget = QueryWorkBudget(work_limits)
    budget.consume_raw_transport_payload_bytes(raw_payload_bytes)
    return budget


def _current_transport_query_work_budget() -> QueryWorkBudget | None:
    if mcp is None:
        return None
    try:
        request = mcp.get_context().request_context.request
    except (LookupError, ValueError):
        return None
    return request if isinstance(request, QueryWorkBudget) else None


mcp: Any = create_trino_mcp(
    trino_mcp_services(budget_provider=_current_transport_query_work_budget)
)


def main() -> None:
    global mcp

    missing = []
    if mcp is None:
        missing.append("mcp")
    if sqlglot is None:
        missing.append("sqlglot")
    if trino is None:
        missing.append("trino")
    if missing:
        raise RuntimeError(
            "Trino MCP support is not installed "
            f"(missing: {', '.join(missing)}); "
            "install agent-paranoid-android[mcp,trino]"
        )
    TrinoConfig.from_env()
    work_limits = query_work_limits_from_env()
    audit_logger_from_env("trino-mcp")
    mcp = create_trino_mcp(
        trino_mcp_services(
            work_limits=work_limits,
            budget_provider=_current_transport_query_work_budget,
        )
    )
    run_bounded_trino_mcp(
        mcp,
        max_payload_bytes=work_limits.raw_transport_payload_bytes,
        request_context_factory=partial(
            _new_transport_query_work_budget,
            work_limits=work_limits,
        ),
    )


if __name__ == "__main__":
    main()
