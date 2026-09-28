"""Private SQL encoding of validated transformation results; never executes SQL."""

from collections.abc import Iterator

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import InputDimension, TransformationLimitError
from test_data_agent.core.privacy import looks_sensitive_value
from test_data_agent.core.transformation_policy import SqlOutput
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.postgres_sql_export import quote_postgres_identifier
from test_data_agent.io.transformation_output import normalized_output_rows


def render_transformation_sql(result: CsvTransformationResult, output: SqlOutput, *,
                              max_bytes: int, budget: GenerationBudget,
                              source_rows: Iterator[tuple[str | None, ...]] | None = None) -> bytes:
    """Encode an exact ordered output schema; caller owns approval and publication."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid SQL output budget")
    if (tuple(item.name for item in output.fields) != result.columns
            or len(set(result.columns)) != len(result.columns)
            or any(looks_sensitive_value(name) for name in (output.table, *result.columns))):
        raise ValueError("invalid SQL output schema")
    payload = bytearray()

    def append(statement: str) -> None:
        budget.check("transformation SQL output")
        encoded = statement.encode("utf-8")
        if len(payload) + len(encoded) > max_bytes:
            raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                len(payload) + len(encoded), max_bytes, "sql_output_run")
        payload.extend(encoded)

    types = {"string": "TEXT", "integer": "BIGINT", "float": "DOUBLE PRECISION", "boolean": "BOOLEAN",
             "date": "DATE", "datetime": "TIMESTAMPTZ"}
    definitions = []
    for item in output.fields:
        shape = item.decimal_type
        sql_type = f"NUMERIC({shape.precision},{shape.scale})" if shape else types[item.type]
        definitions.append(f"{quote_postgres_identifier(item.name)} {sql_type}" + ("" if item.nullable else " NOT NULL"))
    table = quote_postgres_identifier(output.table)
    columns = ", ".join(quote_postgres_identifier(name) for name in result.columns)
    append("BEGIN;\nSET LOCAL standard_conforming_strings = on;\n")
    append(f"CREATE TABLE {table} ({', '.join(definitions)});\n")
    for values, _ in normalized_output_rows(result, output, budget=budget, source_rows=source_rows):
        append(f"INSERT INTO {table} ({columns}) VALUES ({', '.join(values)});\n")
    append("COMMIT;\n")
    return bytes(payload)
