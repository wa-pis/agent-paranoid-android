"""Closed fictional query-result capture; no database client or public wiring.

An injected stream must enforce backend read-only/scan/statement deadlines.
Local result checks cannot interrupt a blocking driver or bound its allocations.
"""

import io
import json
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any

from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_CELLS, DEFAULT_MAX_INPUT_COLUMNS, DEFAULT_MAX_INPUT_FILE_BYTES,
    DEFAULT_MAX_INPUT_ROWS, GenerationBudget, max_parquet_expanded_bytes,
)
from test_data_agent.core.privacy import infer_sensitive_from_name
from test_data_agent.core.transformation_policy import BehaviorPolicy, parse_behavior_policy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader
from test_data_agent.io.transformation_query_snapshot import _capture_query_result
from test_data_agent.sql_query_source import (
    QUERY_SOURCE_POLICY_VERSION, QuerySourceColumn, SqlQueryProfileRequest,
    authorize_query_source, inspect_query_source,
)


@dataclass(frozen=True, repr=False)
class _ResultQuery:
    sql: str = field(repr=False)
    max_rows: int
    adapter: str
    source_id: str
    table: str
    columns: tuple[str, ...]


def _capture_authorized_result(
    request: SqlQueryProfileRequest, *, allowed_tables: frozenset[str],
    source_columns: tuple[QuerySourceColumn, ...], schema: Any,
    stream: Callable[[_ResultQuery], AbstractContextManager[Iterator[Any]]],
    policy: BehaviorPolicy, max_rows: int, max_bytes: int, budget: GenerationBudget,
) -> SnapshotPart:
    """Authorize before callback; bind context/schema/ordered batches exactly.

    Source columns must be the frozen allowlisted metadata, never unrestricted
    discovery. This private development boundary accepts fictional streams only.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        budget.check("query capture preflight")
        if (type(max_rows) is not int or not 0 < max_rows <= DEFAULT_MAX_INPUT_ROWS
                or type(max_bytes) is not int or not 0 < max_bytes <= DEFAULT_MAX_INPUT_FILE_BYTES
                or not isinstance(schema, pa.Schema) or schema.metadata
                or not 0 < len(schema) <= DEFAULT_MAX_INPUT_COLUMNS
                or type(source_columns) is not tuple
                or not 0 < len(source_columns) <= DEFAULT_MAX_INPUT_COLUMNS
                or type(allowed_tables) is not frozenset
                or not 0 < len(allowed_tables) <= DEFAULT_MAX_INPUT_COLUMNS
                or any(type(name) is not str or not name or len(name) > 256 for name in allowed_tables)):
            raise ValueError
        policy = parse_behavior_policy(policy)
        draft = inspect_query_source(request)
        if draft.table_name not in allowed_tables:
            raise ValueError
        plan = authorize_query_source(draft, source_columns)
        if (policy.input_format != f"{plan.adapter.value}_query"
                or tuple(schema.names) != plan.output_fields
                or any(item.entity != plan.entity_name for item in policy.fields)
                or any(infer_sensitive_from_name(item.name) for item in source_columns)):
            raise ValueError
        context = json.dumps({"policy": QUERY_SOURCE_POLICY_VERSION,
            "query": plan.fingerprint, "source": plan.source_id, "entity": plan.entity_name,
            "tables": sorted(allowed_tables), "columns": [
                [item.name, item.data_type, item.nullable] for item in source_columns],
            "max_rows": max_rows, "max_bytes": max_bytes}, sort_keys=True, separators=(",", ":")).encode()
        if len(context) > max_bytes:
            raise ValueError
        bound_schema = schema.with_metadata({b"apa.capture": context})

        class BoundedBuffer(io.BytesIO):
            def write(self, data: Any) -> int:
                budget.check("query capture encoding")
                # Include the fixed envelope, not just the Parquet payload.
                if self.tell() + len(data) + 128 > max_bytes:
                    raise ValueError
                return super().write(data)

        # Reuse native type/format checks before the stream can be opened.
        with BoundedBuffer() as preflight:
            pq.write_table(pa.Table.from_batches([], schema=bound_schema), preflight)
            empty = _capture_query_result(preflight.getvalue(), adapter=policy.input_format,
                query_sha256=plan.fingerprint, entity=plan.entity_name)
            source_reader(empty, policy, budget=budget)
        fields = ", ".join(f'"{name}"' for name in plan.output_fields)
        query = _ResultQuery(
            f'SELECT {fields} FROM ({plan.sql}) AS "__apa_capture" LIMIT {max_rows + 1}',
            max_rows + 1, plan.adapter.value, plan.source_id, draft.table_name,
            tuple(item.name for item in source_columns),
        )
        rows = decoded = 0
        expanded_limit = min(max_bytes, max_parquet_expanded_bytes())
        with BoundedBuffer() as buffer:
            with pq.ParquetWriter(buffer, bound_schema) as writer:
                budget.check("query capture open")
                with stream(query) as batches:
                    for batch in batches:
                        budget.check("query capture batch")
                        if (not isinstance(batch, pa.RecordBatch)
                                or not batch.schema.equals(schema, check_metadata=True)):
                            raise ValueError
                        rows += batch.num_rows
                        decoded += batch.nbytes
                        if (rows > max_rows or rows * len(schema) > DEFAULT_MAX_INPUT_CELLS
                                or decoded > expanded_limit
                                or any(not item.nullable and batch.column(i).null_count
                                       for i, item in enumerate(schema))):
                            raise ValueError
                        writer.write_batch(batch.replace_schema_metadata(bound_schema.metadata))
                    budget.check("query capture stream complete")
            source = _capture_query_result(buffer.getvalue(), adapter=policy.input_format,
                query_sha256=plan.fingerprint, entity=plan.entity_name)
        source_reader(source, policy, budget=budget)
        return source
    except Exception:
        pass
    raise ValueError("invalid bounded query capture")
